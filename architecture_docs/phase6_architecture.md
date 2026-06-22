# Phase 6 架构文档：MCP 集成

---

## 1. 全局架构

```
┌────────────────────────────────────────────────────────────────┐
│  外部 MCP Servers (stdio 子进程)                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ filesystem  │  │ github       │  │ 自定义 Server │           │
│  │ (npx ...)   │  │ (npx ...)    │  │ (python ...) │           │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼────────────────┼─────────────────┼───────────────────┘
          │ stdio          │ stdio           │ stdio
          ▼                ▼                 ▼
┌────────────────────────────────────────────────────────────────┐
│   MCPRuntime (app/services/mcp/runtime.py)                      │
│   ┌────────────────────────────────────────────┐                │
│   │ _clients: {server_name: MCPClient}         │                │
│   │ _tools: {"mcp__<server>__<tool>": McpToolDef} │             │
│   └────────────────────────────────────────────┘                │
│                       │                                         │
│   attach_mcp_runtime()│ 注入                                    │
│                       ▼                                         │
│   ToolRegistry (统一工具入口)                                   │
│   ┌──────────────────────────────────────────────┐              │
│   │ 本地工具：web_search / calculate / get_time  │              │
│   │ MCP 工具：mcp__filesystem__read_file ...     │              │
│   └──────────────────────────────────────────────┘              │
└─────────┬───────────────────────────────────┬───────────────────┘
          │                                   │
          ▼                                   ▼
   ┌──────────────┐                  ┌──────────────────┐
   │  LLM 工具循环 │                  │ /mcp REST 端点   │
   │  (chat / RAG │                  │ servers / tools  │
   │   research)  │                  │ /tools/{n}/invoke│
   └──────────────┘                  └──────────────────┘

  另一面：
┌────────────────────────────────────────────────────────────────┐
│  本项目 ToolRegistry  ──→  build_mcp_server()  ──→  stdio Server │
│                                                                  │
│  入口：python -m scripts.run_mcp_server                          │
│  外部 LLM Agent（Claude Desktop 等）可以连过来用我们的工具      │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. 模块清单

### 2.1 `app/services/mcp/`

| 文件 | 行数 | 职责 |
|------|------|------|
| `adapter.py` | ~30 | OpenAI ↔ MCP schema 互转 |
| `server.py` | ~52 | 把本项目工具暴露为 MCP Server（stdio） |
| `client.py` | ~80 | 单个 MCP Server 连接器 |
| `runtime.py` | ~120 | 多 Server 注册中心 + 工具命名空间路由 |

### 2.2 ToolRegistry 扩展（`app/services/tool_registry.py`）

新增方法：
```python
def attach_mcp_runtime(self, runtime: MCPRuntime) -> None:
    self._mcp_runtime = runtime
    # 把 runtime 的工具元信息合并进自己的 schema 列表
```

执行逻辑：
```python
async def execute(self, name, arguments):
    if name.startswith("mcp__"):
        return await asyncio.wait_for(
            self._execute_mcp_tool(name, arguments),
            timeout=self.settings.tool_call_timeout,
        )
    # ... 走本地工具老路
```

### 2.3 启动 / 关闭顺序（`app/main.py` lifespan）

```python
@asynccontextmanager
async def lifespan(app):
    if settings.mcp_external_servers.strip():
        await init_mcp_runtime(settings)        # 起所有 stdio 子进程
        runtime = get_mcp_runtime()
        tools_routes.tool_registry.attach_mcp_runtime(runtime)
        research_routes.tool_registry.attach_mcp_runtime(runtime)
    try:
        yield
    finally:
        await shutdown_mcp_runtime()             # 干净关掉所有子进程
```

### 2.4 REST 端点（`app/api/routes/mcp.py`）

| Method | Path | 用途 |
|--------|------|------|
| GET | `/api/v1/mcp/servers` | 列出已连接的外部 Server |
| GET | `/api/v1/mcp/tools` | 列出所有 MCP 工具（含命名空间名） |
| POST | `/api/v1/mcp/tools/{name}/invoke` | **调试端点**，直接调用某个 MCP 工具（受 guardrails 保护） |

---

## 3. 关键数据结构

### 3.1 `McpToolDef`（runtime 内部）

```python
@dataclass
class McpToolDef:
    namespaced_name: str    # "mcp__filesystem__read_file"
    server_name: str         # "filesystem"
    tool_name: str           # "read_file"
    description: str
    input_schema: dict       # JSON Schema
```

### 3.2 `mcp_external_servers` 配置格式

`.env`:
```
MCP_EXTERNAL_SERVERS=filesystem:npx -y @modelcontextprotocol/server-filesystem C:\workspace
```

多个 Server 用 `;;;` 分隔（避免与命令里的空格/分号冲突）：
```
MCP_EXTERNAL_SERVERS=filesystem:npx -y ... C:\path;;;github:npx -y @modelcontextprotocol/server-github
```

`parse_external_mcp_servers()`：
1. 按 `;;;` 拆分
2. 第一个 `:` 分 server_name 和 command_line
3. `shlex.split(command_line, posix=(os.name != "nt"))` 拆 argv

---

## 4. Server 端点 vs Client 端点的关键区别

| 维度 | 作为 MCP Server | 作为 MCP Client |
|------|----------------|-----------------|
| 入口 | `python -m scripts.run_mcp_server` | FastAPI 启动时 lifespan |
| 协议方向 | 别人调我们的 ToolRegistry | 我们调别人的工具 |
| 异常处理 | 必须返 isError=True | 必须 wait_for 超时 |
| 鉴权 | 由对方 Client 决定接不接 | 我方 guardrails 白名单 |
| 命名 | 直接用 ToolRegistry 名 | 加 `mcp__<server>__` 前缀 |

---

## 5. 配置项（`Settings`）

```python
mcp_server_name: str = "agent-platform-tools"
mcp_server_version: str = "0.6.0"
mcp_external_servers: str = ""  # CSV-like: name:cmd;;;name:cmd
tool_call_timeout: int = 30  # 秒，所有工具（含 MCP）共享
guardrails_allowed_mcp_tools: str = "*"  # CSV 或 "*"
```

---

## 6. 测试矩阵

| 文件 | 覆盖点 |
|------|--------|
| test_mcp_adapter.py | 双向 schema 转换、缺字段兼容 |
| test_mcp_server.py | call_tool 成功/失败/异常三条路径 |
| test_mcp_client.py | initialize/list_tools/call_tool；连接失败清理 |
| test_mcp_runtime.py | 多 server 命名空间；工具路由 |
| test_mcp_config.py | shlex Windows 兼容；多 server 解析 |
| test_mcp_endpoint.py | 3 个 REST 端点；guardrails 白名单 |
| test_tool_registry_with_mcp.py | attach_mcp_runtime 后老接口不受影响 |

合计 ~50 测试，覆盖 P0 修复点。

---

## 7. 已知限制 / 后续工作

- **只支持 stdio**：HTTP / SSE 传输未实现（社区主流也是 stdio）
- **Resources / Prompts 未实现**：留作课后练习
- **重连**：外部 Server 中途崩了不会自动重连，会让该工具变成"返回 isError 的占位符"
- **观测**：MCP 调用未单独打 trace，目前混在 ToolRegistry 的 trace 里

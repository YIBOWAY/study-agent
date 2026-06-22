# Phase 6：MCP（Model Context Protocol）集成

> 目标：理解 MCP 协议设计；让 Agent 既能**当 MCP Server 暴露工具**，又能**当 MCP Client 调用外部 Server**
> 前置要求：Phase 3（Function Calling）+ Phase 5（多 Agent）
> 预计时间：2-4 天

---

## 0. 为什么需要 MCP

Phase 3 我们写了 `ToolRegistry`：自定义工具注册到字典里，LLM 用 OpenAI Function Calling 协议调用。

但每个团队/项目都自己定一套 ToolRegistry，会带来三个痛点：
1. **重复造轮子**：每个项目都自己写 weather/search/calculator
2. **互不兼容**：A 项目的工具搬不到 B 项目，只能再写一遍
3. **信任难题**：怎么把"第三方工具"安全接进自己的 Agent？

Anthropic 在 2024-11 提出 **MCP（Model Context Protocol）**：
- 把"工具/资源/Prompt 模板"用**标准协议**暴露
- 任何兼容 MCP 的客户端都能立即接入
- 类比 HTTP 之于 Web、LSP 之于 IDE

---

## 1. MCP 的三大原语

| 原语 | 作用 | 类比 |
|------|------|------|
| **Tools** | 可调用函数 | OpenAI Function Calling |
| **Resources** | 可读数据（URI 寻址） | 文件系统 / REST GET |
| **Prompts** | 预定义的 Prompt 模板 | LangChain PromptTemplate |

本项目重点实现 **Tools**（其余两个 spec 一致，可作课后练习）。

---

## 2. 协议要点（精简）

MCP 基于 **JSON-RPC 2.0**，传输层支持 stdio（推荐）/ SSE / HTTP。

最常用的方法：

| 方法 | 方向 | 用途 |
|------|------|------|
| `initialize` | Client → Server | 握手，协商能力 |
| `tools/list` | Client → Server | 列出 Server 暴露的工具 |
| `tools/call` | Client → Server | 调用工具，返回 `CallToolResult` |
| `notifications/initialized` | 双向 | 握手完成 |

**关键点：错误用 `isError=True` 而不是异常**

```python
# 正确
return CallToolResult(
    content=[TextContent(type="text", text="参数错误: ...")],
    isError=True,
)

# 错误（Client 无法区分协议错误和工具错误）
raise ValueError("参数错误")
```

> **本项目踩过的坑**：早期 server.py 直接 raise，导致 Client 看到的是连接级错误，根本拿不到 isError=True。Phase 6 P0 修复就是这条。

---

## 3. 本项目的 MCP 架构

我们做了一件**有教学价值的事**：让我们的 Agent 同时是 **Server** 和 **Client**。

```
┌─────────────────────────────────────────────────────────────┐
│                  app/services/mcp/                           │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ adapter  │   │  server  │   │  client  │   │ runtime  │  │
│  │ .py      │   │  .py     │   │  .py     │   │ .py      │  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘  │
│       │              │              │               │        │
│       │ 互转         │ stdio 暴露  │ stdio 连     │ 多 Server │
│       │ OpenAI/MCP   │ 本地工具    │ 外部 Server  │ 注册中心  │
└───────┼──────────────┼──────────────┼──────────────┼────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   schema 字段    `python -m         npx mcp-      ToolRegistry
   双向映射        scripts.run_      filesystem    .attach_mcp_runtime
                  mcp_server`                       → tool 名空间
                                                    `mcp__<server>__<tool>`
```

### 3.1 `adapter.py` — Schema 互转

OpenAI 工具定义和 MCP Tool 字段名差异：

| OpenAI | MCP |
|--------|-----|
| `function.name` | `name` |
| `function.description` | `description` |
| `function.parameters` (JSON Schema) | `inputSchema` |

`adapter.py` 提供两个函数双向转换，让我们能用同一份 ToolRegistry 同时输出两种 schema。

### 3.2 `server.py` — 把本项目工具暴露成 MCP Server

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [openai_tool_to_mcp_tool(t) for t in tool_registry.get_openai_tools_schema()]

@server.call_tool()
async def call_tool(name, arguments) -> CallToolResult:
    record = await tool_registry.execute(name, arguments)
    if record.error:
        return CallToolResult(content=[TextContent(text=record.error)], isError=True)
    return CallToolResult(content=[TextContent(text=record.result)], isError=False)
```

启动入口：`python -m scripts.run_mcp_server`

### 3.3 `client.py` — 连外部 MCP Server

`MCPClient` 包装 `mcp.ClientSession`，封装：
- `connect()`：启 stdio 子进程 + initialize 握手
- `list_tools()` / `call_tool(name, args)`
- `close()`：通过 AsyncExitStack 兜底清理

### 3.4 `runtime.py` — 多 Server 路由

```python
class MCPRuntime:
    _clients: dict[str, MCPClient]   # server_name -> client
    _tools: dict[str, McpToolDef]    # "mcp__<server>__<tool>" -> 元信息
```

启动时根据 `MCP_EXTERNAL_SERVERS` 环境变量解析多个 stdio 命令并发连接。

工具命名空间格式：`mcp__<server>__<tool>`，例如 `mcp__filesystem__read_file`。这样：
- 与本地工具（`web_search` / `calculate`）不会撞名
- 看到名字就知道来源
- ToolRegistry 拿到 `mcp__` 前缀的工具直接转发到 runtime

---

## 4. 关键修复点（P0 系列，已修复）

| ID | 问题 | 修复 |
|----|------|------|
| P0.1 | `server.py` 异常路径未返回 `isError=True` | 改为构造 CallToolResult |
| P0.2 | MCP 工具调用没有超时 | `asyncio.wait_for(..., settings.tool_call_timeout)` |
| P0.3 | Windows 路径被 shlex POSIX 模式吞了反斜杠 | `shlex.split(cmd, posix=(os.name != "nt"))` |
| P0.4 | `/mcp/tools/{name}/invoke` 调试端点未保护 | 强制走 guardrails 校验 |
| P0.5 | `mcp` 包未锁版本 | requirements.txt 锁 `mcp==1.27.0` |
| P0.6 | Cohere rerank 偶发 403 让请求 500 | 加 `rerank_fail_soft=True`，降级为前 N 候选 |

> **学习要点**：每一个 P0 都对应一个生产事故案例。MCP 看起来简单，**协议错误处理 + 平台兼容 + 超时 + 鉴权**这四件事必须从第一天就做对。

---

## 5. 安全模型

| 风险 | 缓解 |
|------|------|
| 第三方 MCP Server 被植入恶意工具 | Guardrails 白名单 `MCP_ALLOWED_TOOLS=mcp__filesystem__read_file,...` |
| 工具参数被注入命令 | `validate_tool_call` 过滤 `;`、`&&`、`$()`、`powershell` 等模式 |
| 工具消耗大量 token | 强制 timeout + 调用次数上限 |
| stdio 子进程僵尸 | AsyncExitStack 在 connect 失败时也能清理 |
| 调试端点被外网访问 | 默认 dev 才打开；prod 由 `API_KEY_REQUIRED=true` 兜底 |

---

## 6. MCP vs Function Calling vs A2A

| 协议 | 解决什么 | 状态 |
|------|---------|------|
| OpenAI Function Calling | 单个 LLM 厂商 + 单进程内的工具调用 | 事实标准 |
| **MCP** | LLM Agent ↔ 工具/资源 的**跨进程跨厂商**接入 | Anthropic 主导，2024-11 公开，社区生态快速增长 |
| A2A (Agent-to-Agent) | Agent ↔ Agent 之间的协作通信 | Google 提案，仍在演进 |

> **面试提示**：被问"为什么用 MCP 而不是 Function Calling" → "Function Calling 是协议，MCP 是工具的**分发协议**。前者像 HTTP 请求格式，后者像 npm registry。"

---

## 7. 完成本阶段你应当能回答

- [ ] 用一句话说清 MCP 是什么、解决什么
- [ ] Tools / Resources / Prompts 三大原语各自适合什么场景
- [ ] `tools/call` 出错时为什么不能 raise
- [ ] 为什么用 stdio 而不是 HTTP（提示：进程隔离、零端口冲突）
- [ ] 多 Server 工具如何避免命名冲突
- [ ] Windows 上挂载 npx 命令为什么需要特殊处理 shlex

---

## 8. 推荐资料

| 主题 | 资源 |
|------|------|
| MCP 规范 | https://modelcontextprotocol.io |
| 官方 Server 示例 | github.com/modelcontextprotocol/servers |
| Anthropic 博文 | "Introducing the Model Context Protocol" |
| Python SDK 源码 | github.com/modelcontextprotocol/python-sdk |

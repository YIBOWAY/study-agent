# Phase 6（MCP 补齐）— Codex GPT-5.5 长任务 Prompt

> 学习方案对照：Phase 6（多 Agent + MCP + 平台）剩余部分
> 大项目里程碑：里程碑 6（多 Agent 协作系统 + **MCP Server**）补齐
> 前置：Phase 5 已完成（179 tests passing）

---

## 任务总览

为 `8w-plan` 项目增加 **Model Context Protocol (MCP)** 能力，让现有 `ToolRegistry` 中的 5 个工具可通过 MCP 协议被外部 LLM 客户端（Claude Desktop / Cursor / 其他 Agent）消费；同时让本项目的 Agent 能消费来自外部 MCP Server 的工具。

### 学习目标
- 理解 MCP 协议（JSON-RPC 2.0 over stdio/SSE）的核心概念：tools、resources、prompts
- 掌握 MCP Server 实现：把内部工具暴露为标准协议
- 掌握 MCP Client 实现：动态发现并调用外部 MCP 工具
- 理解 MCP 解决了什么问题：工具定义标准化 + 工具复用 + 解耦 Agent 逻辑与工具实现

### 不做什么
- 不实现 SSE 远程传输（仅 stdio，足以验证概念）
- 不实现 MCP Resources / Prompts（仅实现 Tools）
- 不连接真实第三方 MCP Server（用 mock + 自连接验证）

---

## 项目当前状态（Codex 必读）

```
8w-plan/
├── app/
│   ├── main.py                         # 已注册 6 个 router
│   ├── core/config.py                  # Settings（pydantic-settings）
│   ├── services/
│   │   ├── llm_service.py              # LLMService（httpx）
│   │   ├── tool_registry.py            # ToolRegistry — 5 个工具注册
│   │   ├── tools/                      # 5 个内置工具
│   │   │   ├── get_current_time.py
│   │   │   ├── calculate.py
│   │   │   ├── search_knowledge_base.py
│   │   │   ├── web_search.py
│   │   │   └── code_executor.py
│   │   ├── memory_service.py           # Phase 5 新增
│   │   ├── research/                   # workflow / agent / agent_v2
│   │   ├── multi_agent/                # Phase 5 新增
│   │   └── ...（rag / embedding / 等）
│   └── api/routes/
│       └── ...（health / chat / rag / tools / research / memory）
├── tests/                              # 179 tests passing
└── requirements.txt
```

### 现有 ToolRegistry 接口（Codex 必须复用，不修改）

```python
# app/services/tool_registry.py
class ToolRegistry:
    def __init__(self, settings: Settings): ...
    async def execute(self, tool_name: str, arguments: dict) -> ToolCallRecord: ...
    def list_tools(self) -> list[dict]:
        # 返回 OpenAI Function Calling 格式的工具定义列表
        # [{"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}]
    settings: Settings
```

---

## Part A: 依赖与配置

### A.1 新增依赖

在 `requirements.txt` 末尾追加：

```
mcp>=1.2.0
```

> 说明：`mcp` 是 Anthropic 官方 Python SDK（PyPI: `mcp`），实现 MCP 协议规范。它本身只是协议封装，不是 LLM SDK。这与项目"禁止 langchain-openai/openai SDK"的原则不冲突——MCP 是协议，不是 LLM 抽象层。

### A.2 扩展 Settings — `app/core/config.py`

新增字段：

```python
# MCP 配置
mcp_server_name: str = "research-agent-tools"   # 本项目作为 MCP Server 的名称
mcp_server_version: str = "0.1.0"
mcp_external_servers: str = ""
# 格式: "name1:cmd1 args1 args2|name2:cmd2 args"
# 例: "filesystem:npx -y @modelcontextprotocol/server-filesystem /tmp|github:python -m my_gh_server"
# 留空则不连接任何外部 MCP Server
```

提供 helper：

```python
def parse_external_mcp_servers(self) -> list[dict[str, Any]]:
    """解析 mcp_external_servers 配置为 [{name, command, args}, ...]"""
```

---

## Part B: MCP Server — 把内部工具对外暴露

### B.1 模块结构

新增目录 `app/services/mcp/`：

```
app/services/mcp/
├── __init__.py
├── server.py        # MCP Server 实现（暴露 ToolRegistry）
├── client.py        # MCP Client 实现（消费外部 MCP Server）
├── adapter.py       # 工具定义转换（OpenAI ↔ MCP）
└── runtime.py       # 全局运行时（管理已连接的外部 MCP Server）
```

### B.2 `adapter.py`：协议格式转换

```python
# 提供两个纯函数（可独立单元测试）：
#
# def openai_tool_to_mcp_tool(openai_tool: dict) -> mcp.types.Tool:
#     """把 ToolRegistry.list_tools() 的某一项转为 MCP Tool 对象"""
#     # 输入示例:
#     # {"type": "function", "function": {"name": "calculate",
#     #   "description": "Compute a math expression",
#     #   "parameters": {"type": "object", "properties": {...}, "required": [...]}}}
#     # 输出: mcp.types.Tool(name=..., description=..., inputSchema={...})
#
# def mcp_tool_to_openai_tool(mcp_tool: mcp.types.Tool, server_name: str) -> dict:
#     """把外部 MCP Server 的工具转为 OpenAI 格式（前缀 server_name 避免冲突）"""
#     # 输出 name 形如: "mcp__filesystem__read_file"
#     # 这样 ToolRegistry 注册后 LLM 调用时不会与本地工具冲突
#
# 关键: inputSchema 字段就是 OpenAI parameters 的 JSON Schema，几乎可直接复制
```

### B.3 `server.py`：MCP Server 实现

```python
# 用 mcp.server.Server 构建一个把 ToolRegistry 全部工具暴露的 MCP Server
#
# 关键函数：
#
# def build_mcp_server(tool_registry: ToolRegistry, settings: Settings) -> mcp.server.Server:
#     """构造一个 MCP Server，注册所有 ToolRegistry 中的工具"""
#
#     server = Server(name=settings.mcp_server_name, version=settings.mcp_server_version)
#
#     @server.list_tools()
#     async def list_tools() -> list[mcp.types.Tool]:
#         openai_tools = tool_registry.list_tools()
#         return [openai_tool_to_mcp_tool(t) for t in openai_tools]
#
#     @server.call_tool()
#     async def call_tool(name: str, arguments: dict) -> list[mcp.types.TextContent]:
#         # 调用 ToolRegistry.execute()
#         record = await tool_registry.execute(name, arguments)
#         # 把 ToolCallRecord 转为 MCP TextContent
#         text = json.dumps(record.result, ensure_ascii=False) if not record.error else f"ERROR: {record.error}"
#         return [TextContent(type="text", text=text)]
#
#     return server
#
# async def run_stdio_server(tool_registry: ToolRegistry, settings: Settings) -> None:
#     """以 stdio 方式运行 MCP Server（被 client process 通过 stdin/stdout 通信）"""
#     server = build_mcp_server(tool_registry, settings)
#     from mcp.server.stdio import stdio_server
#     async with stdio_server() as (read_stream, write_stream):
#         await server.run(read_stream, write_stream, server.create_initialization_options())
```

### B.4 `scripts/run_mcp_server.py`（新增）

```python
"""
启动本项目的 MCP Server（stdio 模式）。
外部 MCP Client（Claude Desktop / Cursor / 测试客户端）可通过 stdio 连接消费这些工具。

使用方式：
    python -m scripts.run_mcp_server

外部客户端配置示例（claude_desktop_config.json）：
{
  "mcpServers": {
    "research-agent": {
      "command": "python",
      "args": ["-m", "scripts.run_mcp_server"],
      "cwd": "E:/programs/AI_Agent_program/8w-plan"
    }
  }
}
"""
from __future__ import annotations
import asyncio
from app.core.config import get_settings
from app.services.tool_registry import ToolRegistry
from app.services.mcp.server import run_stdio_server

async def main() -> None:
    settings = get_settings()
    registry = ToolRegistry(settings=settings)
    await run_stdio_server(registry, settings)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Part C: MCP Client — 消费外部 MCP Server

### C.1 `client.py`：单连接客户端

```python
# 用 mcp.client 连接到一个外部 MCP Server（stdio 模式）
#
# 类:
#
# class MCPClientConnection:
#     """管理一个到外部 MCP Server 的连接"""
#     def __init__(self, name: str, command: str, args: list[str]):
#         self.name = name
#         self.command = command
#         self.args = args
#         self._session: ClientSession | None = None
#         self._exit_stack: AsyncExitStack | None = None
#         self._tools: list[dict] = []  # OpenAI 格式
#
#     async def connect(self) -> None:
#         """启动子进程并初始化 MCP session，缓存工具列表"""
#         # 用 mcp.client.stdio.stdio_client + ClientSession
#         # 调用 session.list_tools() 获取所有工具
#         # 用 mcp_tool_to_openai_tool() 转换并缓存到 self._tools
#
#     async def call_tool(self, tool_name: str, arguments: dict) -> dict:
#         """调用外部工具，返回结果 dict"""
#         # tool_name 是带前缀的形如 "mcp__filesystem__read_file"
#         # 内部需去掉 "mcp__<server_name>__" 前缀传给 session.call_tool()
#         # 返回 {"result": <text>, "is_error": bool}
#
#     def list_tools(self) -> list[dict]:
#         """返回 OpenAI 格式的工具列表"""
#         return self._tools
#
#     async def close(self) -> None:
#         """关闭子进程"""
```

### C.2 `runtime.py`：MCP 运行时管理器

```python
# 全局运行时，在应用启动时连接所有配置的外部 MCP Server，
# 应用关闭时清理所有连接。
#
# class MCPRuntime:
#     """管理多个 MCPClientConnection"""
#     def __init__(self, settings: Settings):
#         self.settings = settings
#         self._connections: dict[str, MCPClientConnection] = {}
#
#     async def start(self) -> None:
#         """启动所有外部 MCP Server 连接"""
#         for spec in self.settings.parse_external_mcp_servers():
#             conn = MCPClientConnection(spec["name"], spec["command"], spec["args"])
#             try:
#                 await conn.connect()
#                 self._connections[spec["name"]] = conn
#             except Exception as exc:
#                 # 不让单个 server 失败拖垮整个应用
#                 logger.warning(f"MCP server '{spec['name']}' failed to connect: {exc}")
#
#     async def stop(self) -> None:
#         for conn in self._connections.values():
#             await conn.close()
#
#     def list_all_tools(self) -> list[dict]:
#         """返回所有外部 MCP 工具的 OpenAI 格式定义"""
#         tools = []
#         for conn in self._connections.values():
#             tools.extend(conn.list_tools())
#         return tools
#
#     async def execute_tool(self, prefixed_name: str, arguments: dict) -> dict:
#         """根据工具前缀路由到对应的 connection"""
#         # 从 "mcp__<server_name>__<tool>" 中提取 server_name
#         # 调用对应 connection.call_tool()
#
# 模块级 singleton:
# _runtime: MCPRuntime | None = None
# def get_mcp_runtime() -> MCPRuntime: ...
# async def init_mcp_runtime(settings: Settings) -> None: ...
# async def shutdown_mcp_runtime() -> None: ...
```

### C.3 集成到 ToolRegistry

**不修改 `tool_registry.py` 的现有方法**，而是扩展：

```python
# 在 ToolRegistry 中新增 (向后兼容):
#
# def attach_mcp_runtime(self, runtime: MCPRuntime) -> None:
#     """挂载 MCP runtime，使外部工具可被 list_tools() 和 execute() 看见"""
#     self._mcp_runtime = runtime
#
# 修改 list_tools():
#   原本返回内部工具
#   现在: 内部工具 + (mcp_runtime.list_all_tools() if attached else [])
#
# 修改 execute():
#   原本: 检查 tool_name 是否在 _tools dict 中
#   现在:
#     - 如果 tool_name 以 "mcp__" 开头 → 路由到 mcp_runtime.execute_tool()
#     - 否则走原逻辑
#
# 注意: 必须保证未挂载 runtime 时行为完全不变（Phase 4/5 测试不能挂）
```

### C.4 应用生命周期集成 — 修改 `app/main.py`

```python
# 用 FastAPI lifespan 启动/关闭 MCP runtime
#
# from contextlib import asynccontextmanager
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     settings = get_settings()
#     if settings.mcp_external_servers.strip():
#         await init_mcp_runtime(settings)
#     yield
#     await shutdown_mcp_runtime()
#
# app = FastAPI(title=..., debug=..., lifespan=lifespan)
#
# 注意: 默认 mcp_external_servers 为空字符串时，不启动 runtime，
# 保证测试和最小部署不需要任何外部 MCP Server 进程。
```

---

## Part D: API 端点（可选但推荐）

### D.1 新增 `app/api/routes/mcp.py`

```python
# GET /api/v1/mcp/servers
#   返回已连接的外部 MCP Server 列表
#   响应: {"servers": [{"name": "...", "tool_count": N, "tools": [...]}, ...]}
#
# GET /api/v1/mcp/tools
#   返回所有外部 MCP 工具（OpenAI 格式）
#   响应: {"tools": [...], "total": N}
#
# POST /api/v1/mcp/tools/{tool_name}/invoke
#   直接调用某个 MCP 工具（用于调试）
#   请求: {"arguments": {...}}
#   响应: {"result": "...", "is_error": bool}
```

### D.2 在 `main.py` 注册 router

---

## Part E: 测试要求

### E.1 单元测试

**`tests/test_mcp_adapter.py`**（新增）
- `test_openai_to_mcp_basic`: 验证一个简单工具定义能正确转换
- `test_openai_to_mcp_required_fields`: 验证 required 字段保留
- `test_mcp_to_openai_with_prefix`: 验证 server_name 前缀正确添加
- `test_mcp_to_openai_round_trip`: 一个工具 OpenAI→MCP→OpenAI 后保持语义

**`tests/test_mcp_server.py`**（新增）
- `test_build_mcp_server_lists_all_registry_tools`: 用 mock ToolRegistry，验证 server 的 list_tools handler 返回正确数量
- `test_mcp_server_call_tool_success`: mock ToolRegistry.execute() 返回成功，验证 server 返回 TextContent
- `test_mcp_server_call_tool_error`: mock ToolRegistry.execute() 抛错，验证 server 返回 ERROR 文本

**`tests/test_mcp_client.py`**（新增）
- `test_mcp_client_connect_and_list`: 用 mock `stdio_client` + `ClientSession`，验证连接后能获取工具列表
- `test_mcp_client_call_tool_strips_prefix`: 验证调用时正确去除前缀
- `test_mcp_client_handles_connection_error`: 连接失败时优雅退出
- 测试时**禁止**真实启动子进程；用 `unittest.mock` patch `mcp.client.stdio.stdio_client` 和 `ClientSession`

**`tests/test_mcp_runtime.py`**（新增）
- `test_runtime_start_with_no_servers`: 空配置时不抛异常
- `test_runtime_start_skips_failed_server`: 一个失败一个成功时只有成功的被加载
- `test_runtime_list_all_tools_aggregates`: 多个 server 的工具被正确合并
- `test_runtime_execute_routes_to_correct_server`: 根据前缀路由

**`tests/test_mcp_endpoint.py`**（新增）
- `test_get_servers_when_runtime_not_initialized`: 返回空列表
- `test_get_tools_endpoint`: mock runtime，验证响应格式
- `test_invoke_tool_endpoint_success` / `test_invoke_tool_endpoint_error`

### E.2 集成测试

**`tests/test_tool_registry_with_mcp.py`**（新增）
- `test_tool_registry_without_mcp_unchanged`: 验证未挂载 runtime 时行为完全不变（重要！保证 Phase 4/5 测试不挂）
- `test_tool_registry_with_mcp_lists_combined_tools`: 挂载 mock runtime 后 list_tools() 返回内部+外部工具
- `test_tool_registry_with_mcp_routes_external_tool`: 调用 `mcp__xxx__yyy` 路由到 runtime

### E.3 手工 smoke test（不在 pytest 中）

新建 `scripts/smoke_test_mcp.py`：
```python
"""
启动本项目的 MCP Server，再用 MCP Client 连接它自己，
列出工具并调用 calculate，验证端到端工作。
"""
# 使用 subprocess 启动 run_mcp_server.py
# 用 MCPClientConnection 连接它
# 调用 calculate(expression="2+2") 验证结果
# 这是 manual smoke test，不进 pytest
```

---

## 实现顺序（Codex 应该按此推进）

1. `requirements.txt` — 加 `mcp>=1.2.0`，运行 `pip install mcp`
2. `app/core/config.py` — 加 mcp_* 字段 + parse_external_mcp_servers()
3. `app/services/mcp/__init__.py` + `adapter.py`
4. `tests/test_mcp_adapter.py` — 跑通
5. `app/services/mcp/server.py`
6. `tests/test_mcp_server.py` — 跑通
7. `scripts/run_mcp_server.py`
8. `app/services/mcp/client.py`
9. `tests/test_mcp_client.py` — 跑通
10. `app/services/mcp/runtime.py`
11. `tests/test_mcp_runtime.py` — 跑通
12. 修改 `app/services/tool_registry.py`（最小侵入扩展）
13. `tests/test_tool_registry_with_mcp.py` — 跑通
14. 验证: `python -m pytest tests/test_tool_registry.py -v` Phase 3 旧测试仍通过
15. `app/api/routes/mcp.py`
16. `tests/test_mcp_endpoint.py` — 跑通
17. 修改 `app/main.py`：注册 mcp_router + lifespan
18. `scripts/smoke_test_mcp.py`（manual）
19. 全量 `python -m pytest -q` —— 应有 **179 + ~25 = ~204 tests**，全部通过

---

## 完成标准（Codex 自检清单）

- [ ] 所有 179 旧测试仍通过
- [ ] 新增 ~25 个 MCP 相关测试全部通过
- [ ] `python -m scripts.run_mcp_server` 能启动（手动验证：能看到 stdin 等待输入）
- [ ] `scripts/smoke_test_mcp.py` 端到端跑通
- [ ] `GET /api/v1/mcp/tools` 在未配置外部 server 时返回空列表，配置后返回工具列表
- [ ] `ToolRegistry` 在未挂载 runtime 时行为完全不变
- [ ] 工具调用路由：本地工具走原路径，`mcp__*` 工具走 MCP runtime
- [ ] 没有引入除 `mcp` 之外的新依赖
- [ ] 不修改 Phase 4/5 任何代码或测试

---

## Commit Message 模板

```
feat(phase6): add MCP server and client integration

- Add mcp>=1.2.0 dependency
- Implement MCP server exposing all ToolRegistry tools (stdio transport)
- Implement MCP client connecting to external MCP servers
- Add MCPRuntime for lifecycle management
- Extend ToolRegistry to optionally route to external MCP tools
- Add /api/v1/mcp/* endpoints for inspection and debug
- Add scripts/run_mcp_server.py entry point

Tests: 179 → ~204 (all passing)
Refs: docs/Agent开发完整学习方案.md Phase 6 / Milestone 6
```

---

## 设计哲学（写给 Codex）

**为什么单独引入 `mcp` 包，但不引入 `langchain-openai`？**

`mcp` 是**协议定义层**（Anthropic 主导的开放标准），不是 LLM 抽象层。它解决的是"工具如何标准化暴露"的问题，与"LLM API 如何抽象"是两个独立的关注点。引入 `mcp` 等同于引入 `httpx`：协议/传输层的工具，不绕过我们对 LLM 调用的底层理解。

**为什么 stdio 而非 SSE？**

教学项目优先使用最简单的传输方式。stdio 模式让 server/client 通过标准输入输出通信，调试容易，不需要网络配置。SSE 是生产级远程传输，可作为 Phase 8 的扩展。

**MCP 的工程价值**

学完后你能在简历上写："使用 MCP 协议标准化 Agent 的工具接入层，使工具实现与 Agent 逻辑解耦，支持外部 MCP Server 动态扩展工具集。"

# Phase 3: Tool Use & Function Calling — Claude Code 实现 Prompt

## 项目背景

这是一个 AI Agent 8 周学习项目，使用 FastAPI 后端。当前已完成：

- **Phase 0**: Python 工程基础 — 项目脚手架、FastAPI 服务、Settings (pydantic-settings)、pytest
- **Phase 1**: LLM 基础 — 通用 /chat 端点、/extract 端点、Prompt Service
- **Phase 2**: RAG 系统 — 文档解析 (docling)、分块、embedding (text-embedding-3-large, 3072 dim)、Qdrant 向量检索、Cohere rerank、/rag/ingest + /rag/search + /rag/ask 端点

## 技术栈约束

| 依赖 | 版本 | 备注 |
|------|------|------|
| Python | 3.11 | conda env `ai-agent` |
| FastAPI | 0.115.0 | |
| pydantic | 2.9.2 | |
| pydantic-settings | 2.5.2 | |
| httpx | 0.27.2 | **唯一 HTTP 客户端，禁止引入 openai SDK 或 requests** |
| pytest | 8.3.3 | pytest-asyncio, asyncio_mode=auto |

**LLM 提供商**: xairouter (`https://api.xairouter.com/v1`)，兼容 OpenAI chat/completions 格式（包括 function calling / tools 参数）。

**关键约束**:
- xairouter 的 embedding 端点**不支持** `dimensions` 参数，不要在 embedding payload 中发送它
- 所有 HTTP 调用用 httpx.AsyncClient，不引入新的 HTTP 库
- 保持现有项目分层架构: `app/core/`, `app/schemas/`, `app/services/`, `app/api/routes/`
- 新代码需要配套 pytest 单元测试（mock 外部 API 调用）
- 响应和注释用英文，但工具的 description 可以用中文

## 当前项目结构

```
8w-plan/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app, 注册 routers
│   ├── core/
│   │   ├── config.py                   # Settings (pydantic-settings)
│   │   └── logging.py
│   ├── schemas/
│   │   ├── chat.py                     # ChatRequest/Response, ExtractRequest/Response
│   │   └── rag.py                      # SearchRequest/Response, AskRequest/Response
│   ├── services/
│   │   ├── llm_service.py              # LLMService._call_chat_api() — 纯 httpx 调用
│   │   ├── prompt_service.py           # 系统提示词常量
│   │   ├── embedding_service.py
│   │   ├── chunking_service.py
│   │   ├── document_parser_service.py
│   │   ├── vector_store_service.py
│   │   ├── retrieval_service.py
│   │   ├── rerank_service.py
│   │   ├── rag_service.py
│   │   └── evaluation_service.py
│   └── api/routes/
│       ├── health.py
│       ├── chat.py                     # /api/v1/chat, /api/v1/extract
│       └── rag.py                      # /api/v1/rag/ingest, search, ask
├── tests/                              # 79 个通过的 pytest 测试
├── eval/
├── study_docs/
├── requirements.txt
├── pytest.ini                          # asyncio_mode = auto
└── .env
```

## Phase 3 目标

实现 **Tool Use / Function Calling** 能力，让 LLM 能决策并调用外部工具。

### 核心知识点
- OpenAI-compatible Function Calling 机制（tools 参数 + tool_calls 响应）
- 工具定义（JSON Schema）
- 参数提取与验证（Pydantic）
- 多轮工具调用循环
- 并行工具调用处理
- 错误处理与安全（工具白名单、max iterations）

### 阶段产出物
1. **多工具助手**：至少 3 个工具的 Function Calling 端点
2. **工具注册表**：可扩展的工具定义与执行机制
3. **错误处理**：工具调用失败的 graceful handling
4. **单元测试**：覆盖工具调用的各个环节

## 具体实现要求

### 1. Tool Registry（工具注册表）— `app/services/tool_registry.py`

创建一个工具注册和分发系统：

```python
# 设计要求：
# - 每个工具由 (name, description, parameters_schema, handler) 四元组组成
# - parameters_schema 遵循 OpenAI tools 格式的 JSON Schema
# - handler 是 async callable，接收解析后的参数，返回 str 或 dict
# - 提供 register_tool() 和 get_openai_tools_schema() 方法
# - 工具白名单机制：execute 时验证工具名在注册表中
# - 未注册的工具调用 → 抛出明确错误
```

### 2. 内置工具实现 — `app/services/tools/`

实现至少 3 个工具：

**工具 A: `get_current_time`**
- 返回当前时间（支持指定时区，默认 Asia/Shanghai）
- 参数: `timezone` (string, optional)
- 纯本地工具，无外部依赖

**工具 B: `calculate`**
- 安全的数学计算器（四则运算、幂运算等）
- 参数: `expression` (string, required)
- **安全要求**: 禁止 eval()，使用 ast.literal_eval 或白名单运算符手动解析
- 支持基本函数: sqrt, abs, round

**工具 C: `search_knowledge_base`**
- 调用已有的 RAG search 能力（复用 Phase 2 的 retrieval + rerank）
- 参数: `query` (string, required), `top_k` (integer, optional, default=3)
- 返回检索结果摘要
- 这是 RAG + Tool Use 的结合点

### 3. Tool Calling Loop — 扩展 `app/services/llm_service.py`

在 LLMService 中新增方法，实现工具调用循环：

```python
# 新增方法签名：
async def chat_with_tools(
    self,
    user_message: str,
    tools: list[dict],          # OpenAI tools schema
    tool_executor: Callable,    # async (name, args) -> str
    max_iterations: int = 5,    # 防止无限循环
    system_prompt: str | None = None,
) -> dict:
    """
    实现 tool calling loop:
    1. 发送带 tools 的 chat completions 请求
    2. 如果响应包含 tool_calls，逐个执行工具
    3. 将工具结果以 role=tool 追加到 messages
    4. 重新请求 LLM，重复直到 LLM 返回纯文本或达到 max_iterations
    5. 返回 {reply, model, tool_calls_made} 
    
    关键：
    - _call_chat_api 需要扩展支持 tools 参数和解析 tool_calls 响应
    - 处理并行工具调用（一次响应中多个 tool_calls）
    - 每轮工具调用需要 try/except，失败时将错误信息作为 tool result 返回给 LLM
    """
```

### 4. API 端点 — `app/api/routes/tools.py`

```
POST /api/v1/tools/chat
```

请求体：
```json
{
    "message": "北京现在几点了？顺便帮我算一下 23 * 47",
    "enabled_tools": ["get_current_time", "calculate", "search_knowledge_base"],
    "max_iterations": 5
}
```

响应体：
```json
{
    "reply": "北京现在是 2026-04-18 22:30:00。23 × 47 = 1081。",
    "model": "gpt-5.4",
    "tool_calls_made": [
        {"tool": "get_current_time", "args": {"timezone": "Asia/Shanghai"}, "result": "..."},
        {"tool": "calculate", "args": {"expression": "23 * 47"}, "result": "1081"}
    ]
}
```

同时提供工具列表端点：
```
GET /api/v1/tools/list — 返回所有已注册工具的 schema
```

### 5. Schemas — `app/schemas/tools.py`

```python
# ToolChatRequest: message, enabled_tools (optional list[str]), max_iterations (default=5)
# ToolCallRecord: tool (str), args (dict), result (str), error (str | None)  
# ToolChatResponse: reply (str), model (str), tool_calls_made (list[ToolCallRecord])
# ToolInfo: name, description, parameters
# ToolListResponse: tools (list[ToolInfo])
```

### 6. 配置 — 扩展 `app/core/config.py`

新增：
```
TOOL_CALL_MAX_ITERATIONS=10        # 全局默认上限
TOOL_CALL_TIMEOUT=30               # 单个工具执行超时(秒)
```

### 7. 测试要求

在 `tests/` 下新增测试，覆盖：

- **test_tool_registry.py**: 注册、获取 schema、执行、未注册工具报错
- **test_tools_builtin.py**: 每个内置工具的正常/边界/异常用例
  - calculate: 正常表达式、除零、注入攻击（`__import__`）、超长表达式
  - get_current_time: 默认时区、指定时区、无效时区
  - search_knowledge_base: mock RAG 调用、空结果
- **test_tool_calling_loop.py**: mock LLM API 响应，测试：
  - 单轮调用（LLM 返回 1 个 tool_call → 执行 → LLM 返回文本）
  - 多轮调用（LLM 连续调用工具 2-3 次）
  - 并行调用（一次响应中多个 tool_calls）
  - max_iterations 达到上限时的行为
  - 工具执行失败时 LLM 收到错误信息
- **test_tools_endpoint.py**: API 集成测试（mock LLM + mock 工具）

所有测试使用 mock，不调用真实 LLM API。

### 8. main.py 注册

在 `app/main.py` 中注册新 router：
```python
from app.api.routes.tools import router as tools_router
app.include_router(tools_router)
```

## 实现顺序建议

1. `app/core/config.py` — 新增配置项
2. `app/schemas/tools.py` — 数据模型
3. `app/services/tool_registry.py` — 注册表核心
4. `app/services/tools/` — 3 个内置工具
5. `app/services/llm_service.py` — 扩展 tool calling loop
6. `app/api/routes/tools.py` — API 端点
7. `app/main.py` — 注册 router
8. `tests/` — 全部测试
9. 运行 `python -m pytest` 确保全部通过（包括之前 79 个老测试）

## 代码规范

- 遵循现有代码风格：类型注解、async/await、依赖注入
- 新文件需要在对应 `__init__.py` 中暴露（如果需要）
- 保持服务层可测试：通过构造函数注入依赖，避免在函数体中硬编码 get_settings()
- 错误处理：工具内部异常不应让整个请求 500，应被捕获并作为工具执行结果反馈给 LLM
- 不要修改现有测试（除非新代码导致旧接口签名变化，那需要同步更新）

## 完成标准

- [ ] 3+ 内置工具正常工作
- [ ] Tool calling loop 支持多轮和并行调用
- [ ] max_iterations 防止无限循环
- [ ] 工具白名单安全机制
- [ ] calculate 工具无 eval() 注入风险
- [ ] 所有新测试通过
- [ ] 所有 79 个旧测试仍然通过
- [ ] `POST /api/v1/tools/chat` 能处理需要多工具协作的复杂问题

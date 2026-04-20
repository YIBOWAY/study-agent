# Phase 4: Workflow & Agent — Claude Code 实现 Prompt

## 项目背景

这是一个 AI Agent 8 周学习项目，使用 FastAPI 后端。当前已完成：

- **Phase 0**: Python 工程基础 — 项目脚手架、FastAPI 服务、Settings (pydantic-settings)、pytest
- **Phase 1**: LLM 基础 — 通用 /chat 端点、/extract 端点、Prompt Service
- **Phase 2**: RAG 系统 — 文档解析 (docling)、分块、embedding (text-embedding-3-large, 3072 dim)、Qdrant 向量检索、Cohere rerank、/rag/ingest + /rag/search + /rag/ask 端点
- **Phase 3**: Tool Use — 工具注册表、3 个内置工具 (get_current_time / calculate / search_knowledge_base)、Tool Calling Loop、/tools/chat + /tools/list 端点

## 技术栈约束

| 依赖 | 版本 | 备注 |
|------|------|------|
| Python | 3.11 | conda env `ai-agent` |
| FastAPI | 0.115.0 | |
| pydantic | 2.9.2 | |
| pydantic-settings | 2.5.2 | |
| httpx | 0.27.2 | **唯一 HTTP 客户端，禁止引入 openai SDK、tavily-python SDK 或 requests** |
| pytest | 8.3.3 | pytest-asyncio, asyncio_mode=auto |
| **langgraph** | 最新稳定版 | **Phase 4 新增** — 仅用于图编排，不使用 langchain-openai 等 LLM 封装 |

**LLM 提供商**: xairouter (`https://api.xairouter.com/v1`)，兼容 OpenAI chat/completions 格式。

**关键约束**:
- 所有 LLM 调用仍然通过现有的 `LLMService`（httpx），**不引入 langchain-openai / ChatOpenAI 等 LLM 封装**
- Tavily Search 使用 httpx 直接调用 REST API，**不引入 tavily-python SDK**
- LangGraph 仅用于状态图编排（StateGraph、节点、边、条件路由）
- 保持现有项目分层架构: `app/core/`, `app/schemas/`, `app/services/`, `app/api/routes/`
- 新代码需要配套 pytest 单元测试（mock 外部 API 调用）
- 如果 langgraph 安装时附带了 langchain-core，这是正常的，但代码中**不要用 langchain 的 ChatModel / LLM 抽象**

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
│   │   ├── rag.py                      # SearchRequest/Response, AskRequest/Response
│   │   └── tools.py                    # ToolChatRequest/Response, ToolInfo
│   ├── services/
│   │   ├── llm_service.py              # LLMService.chat(), .extract(), .chat_with_tools()
│   │   ├── prompt_service.py           # 系统提示词常量
│   │   ├── tool_registry.py            # ToolRegistry — 工具注册/执行
│   │   ├── tools/                      # 3 个内置工具（Phase 4 将扩展为 5 个）
│   │   │   ├── __init__.py
│   │   │   ├── get_current_time.py
│   │   │   ├── calculate.py
│   │   │   └── search_knowledge_base.py
│   │   ├── embedding_service.py
│   │   ├── chunking_service.py
│   │   ├── document_parser_service.py
│   │   ├── vector_store_service.py
│   │   ├── retrieval_service.py
│   │   ├── rerank_service.py
│   │   ├── rag_service.py              # RAGService.search(), .ask(), .ingest_pdf()
│   │   └── evaluation_service.py
│   └── api/routes/
│       ├── health.py
│       ├── chat.py                     # /api/v1/chat, /api/v1/extract
│       ├── rag.py                      # /api/v1/rag/ingest, search, ask
│       └── tools.py                    # /api/v1/tools/chat, /api/v1/tools/list
├── tests/                              # 103 个通过的 pytest 测试
├── requirements.txt
├── pytest.ini                          # asyncio_mode = auto
└── .env
```

**已有的关键 Service 接口**（Phase 4 需要复用）：

```python
# LLMService（app/services/llm_service.py）
class LLMService:
    def __init__(self, settings: Settings | None = None): ...
    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        # 返回 {"reply": "...", "model": "..."}
    async def chat_with_tools(self, user_message: str, tools: list[dict],
                               tool_registry: ToolRegistry, ...) -> dict:
        # 返回 {"reply": "...", "model": "...", "tool_calls_made": [...]}

# RAGService（app/services/rag_service.py）
class RAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict:
        # 返回 {"results": [...], "embedding_model": "...", "rerank_model": "..."}
    async def ask(self, query: str, top_k: int, final_k: int, ...) -> dict:
        # 返回 {"answer": "...", "sources": [...], "model": "...", "rerank_model": "..."}
```

## Phase 4 目标

Phase 4 有两大任务：

1. **补齐工具层**：新增 Web 搜索（Tavily）和沙箱代码执行两个工具，对齐项目主线里程碑 3 的交付标准
2. **实现 Workflow & Agent**：用同一个"研究助理"任务展示确定性工作流和 LLM 驱动 Agent 的区别

---

## Part A: 新增工具（补齐里程碑 3）

### A1. Tavily Web Search 工具 — `app/services/tools/web_search.py`

**Tavily API 信息**：
- 端点：`POST https://api.tavily.com/search`
- 认证：`Authorization: Bearer <TAVILY_API_KEY>`
- 计划：Researcher (免费 1000 credits/月)
- 文档：https://docs.tavily.com/documentation/api-reference/endpoint/search

**实现要求**：

```python
# 工具名: web_search
# 描述: Search the web for real-time information using Tavily Search API.
# 参数:
#   query: str (required) — 搜索查询
#   max_results: int (optional, default=5, range 1-10) — 返回结果数
#   search_depth: str (optional, default="basic") — "basic" 或 "advanced"
#   topic: str (optional, default="general") — "general", "news", 或 "finance"
#
# handler 实现:
#   1. 用 httpx.AsyncClient POST https://api.tavily.com/search
#   2. 请求体: {"query": ..., "max_results": ..., "search_depth": ..., "topic": ...}
#   3. Header: {"Authorization": "Bearer <key>", "Content-Type": "application/json"}
#   4. 解析响应中的 results 数组
#   5. 每条结果提取: title, url, content (摘要文本)
#   6. 格式化为编号列表返回，每条包含 title + url + content 截断到 300 字符
#   7. 无结果时返回 "No web search results found."
#   8. API 错误时抛出 ValueError，包含状态码和错误信息
#
# 安全:
#   - query 不能为空
#   - max_results 限制 1-10
#   - 不暴露 API key 到返回结果中
```

工厂函数签名：`build_web_search_tool(settings: Settings) -> BuiltinTool`

### A2. 沙箱代码执行工具 — `app/services/tools/code_executor.py`

**实现要求**：

```python
# 工具名: execute_python
# 描述: Execute a Python code snippet in a sandboxed subprocess and return stdout/stderr.
# 参数:
#   code: str (required) — 要执行的 Python 代码
#   timeout: int (optional, default=10, range 1-30) — 执行超时秒数
#
# handler 实现:
#   1. 将 code 写入临时文件（tempfile.NamedTemporaryFile, suffix=".py"）
#   2. 用 asyncio.create_subprocess_exec 执行: [sys.executable, temp_file_path]
#   3. 通过 process.communicate(timeout=timeout) 捕获 stdout + stderr
#   4. 超时时 process.kill()，返回超时错误信息
#   5. 返回格式: "Exit code: {code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
#   6. stdout/stderr 各自截断到 2000 字符（防止输出爆炸）
#   7. 执行完毕后清理临时文件（finally 块）
#
# 安全措施（全部在代码中实现）:
#   - code 长度上限: 5000 字符
#   - 超时硬限制: 最多 30 秒
#   - 使用 subprocess（独立进程），不是 exec/eval（不在当前进程执行）
#   - 禁止关键词黑名单检查（在执行前）:
#     ["import os", "import sys", "import subprocess", "import shutil",
#      "__import__", "eval(", "exec(", "open(", "rm ", "del ",
#      "import socket", "import http", "import requests"]
#     命中时返回错误信息（不执行），说明哪个关键词被拦截
#   - 注意: 黑名单不是银弹，这是教学级别的安全措施
#     生产环境应使用 Docker 容器 / nsjail / gVisor 等真正的沙箱
```

工厂函数签名：`build_code_executor_tool() -> BuiltinTool`

### A3. 配置 — 扩展 `app/core/config.py`

新增 Tavily 配置：
```python
tavily_api_key: str = ""           # Tavily Search API key
tavily_base_url: str = "https://api.tavily.com"  # Tavily API base URL
```

`tavily_api_key` 加入 `normalize_optional_text` 的 field_validator 列表。

### A4. `.env` 配置

```env
# ─── Tavily Web Search ───
TAVILY_API_KEY=tvly-dev-xxxxxxxxxxxxxxxxxxxxxxxx
```

### A5. 注册到 ToolRegistry

在 `app/services/tool_registry.py` 的 `_register_defaults()` 中新增两个工具的注册。
同时更新 `app/services/tools/__init__.py` 导出新的工厂函数。

### A6. 新工具测试

- **test_tools_builtin.py** 中新增（追加到现有文件）：
  - `test_web_search_success`: mock httpx 响应，验证格式化输出
  - `test_web_search_empty`: mock 空结果
  - `test_web_search_api_error`: mock 非 200 响应，验证 ValueError
  - `test_web_search_empty_query`: 空查询验证
  - `test_code_executor_success`: 执行 `print(1+1)`，验证 stdout 包含 "2"
  - `test_code_executor_timeout`: mock 超时场景
  - `test_code_executor_blocked_keyword`: 尝试 `import os`，验证被拦截
  - `test_code_executor_too_long`: 超 5000 字符的代码，验证被拒绝
  - `test_code_executor_stderr`: 执行有语法错误的代码，验证 stderr 输出

---

## Part B: Workflow & Agent 研究助理

### 目标

实现 **Workflow 和 Agent 两种模式的"研究助理"系统**，用同一个任务展示确定性工作流和 LLM 驱动 Agent 的区别。

### 场景设计

用户提供一个研究主题（topic），系统完成以下工作：
1. 将主题重写为优化的搜索查询
2. **多源搜索**：同时搜索本地知识库（RAG）和网络（Tavily），合并结果
3. 评估搜索结果是否充分
4. 如果不充分，换一个角度重新搜索（Agent 独有的循环能力）
5. 将所有搜索结果整合为一份结构化研究报告

**Workflow 版**：路径固定（搜索一次 → 直接生成报告），永远走同一条路
**Agent 版**：LLM 动态决策（评估结果 → 可能搜索多次 → 满意后才生成报告）

### 核心知识点
- Workflow vs Agent 的本质区别（确定性 vs LLM 驱动决策）
- LangGraph StateGraph：节点、边、条件边
- TypedDict 状态管理 + Annotated reducer（列表累积）
- LLM 作为 Router（conditional edge 的判断函数调 LLM）
- 图中循环（search → evaluate → refine → search → ...）
- 迭代上限 / 停止条件设计
- Action trace（每个节点记录自己做了什么）
- Checkpoint / Human-in-the-loop 概念（选做）

### 阶段产出物
1. **Workflow 版研究助理**：确定性流水线
2. **Agent 版研究助理**：LLM 驱动的搜索-评估循环
3. **共享节点函数**：两个 Graph 复用相同的节点实现
4. **API 端点**：两个入口 + 对比能力
5. **Action trace**：完整的执行步骤记录
6. **单元测试**：覆盖节点、图执行、端点

## 具体实现要求

### 1. 新增依赖 — `requirements.txt`

```
langgraph>=0.2.0
```

安装后检查 `from langgraph.graph import StateGraph, END` 能正常导入。

> **注意**: Tavily 和代码执行不需要新增依赖。Tavily 用 httpx 直调 REST API，代码执行用 asyncio.create_subprocess_exec（标准库）。

### 2. 状态定义 — `app/services/research/state.py`

使用 TypedDict + Annotated 定义研究状态：

```python
# 设计要求：
# - topic: str — 用户的研究主题
# - queries: Annotated[list[str], operator.add] — 所有搜过的查询（累积）
# - search_results: Annotated[list[dict], operator.add] — 所有搜索结果（累积）
#     每条结果包含: {"source": "knowledge_base"|"web", "query": str, "text_snippet": str, "score": float, "title": str, "url": str|None}
# - report: str — 最终研究报告
# - steps: Annotated[list[dict], operator.add] — Action trace（累积）
#     每条: {"node": "...", "action": "...", "output_summary": "...", "timestamp": "..."}
# - iteration: int — 当前搜索轮次（从 0 开始）
# - max_iterations: int — 最大搜索轮次
# - evaluation: str — LLM 对结果的评估（"sufficient" | "needs_more" | ""）
#
# 使用 Annotated[list, operator.add] 让 LangGraph 自动合并列表
# 非列表字段（report, iteration, evaluation）采用覆盖语义
```

### 3. 节点实现 — `app/services/research/nodes.py`

创建 5 个节点函数，供 Workflow 和 Agent Graph 共享：

**节点 A: `rewrite_query`**
- 输入：state.topic
- 逻辑：调用 LLMService.chat()，让 LLM 把用户主题重写为一个更适合语义搜索的查询
- 输出：更新 queries（追加新查询）、更新 steps
- System prompt 示例："You are a search query optimizer. Given a research topic, rewrite it into a concise, specific search query optimized for semantic search. Return ONLY the query, no explanation."

**节点 B: `search`**（多源搜索）
- 输入：state.queries[-1]（最新查询）
- 逻辑：**并行执行两个搜索**（用 asyncio.gather）：
  - 调用 RAGService.search() 搜索本地知识库
  - 调用 web_search 工具（通过 ToolRegistry.execute）搜索网络
- 对 RAG 结果：每条标记 `source: "knowledge_base"`，提取 text_snippet / score
- 对 Web 结果：解析 web_search 返回的文本，每条标记 `source: "web"`，提取 title / url / content
- 如果任一源搜索失败，不阻塞另一源（try/except 分别处理，在 steps 中记录错误）
- 如果 Tavily API key 未配置（空字符串），跳过 web search，只用知识库结果
- 输出：更新 search_results（追加新结果）、更新 steps、iteration += 1
- 每条 search_result 保存 {source, query, text_snippet, score, title, url}

**节点 C: `evaluate_results`**（仅 Agent 版使用）
- 输入：state.topic + state.search_results
- 逻辑：调用 LLMService.chat()，让 LLM 评估当前搜索结果是否充分回答研究主题
- 输出：更新 evaluation（"sufficient" 或 "needs_more"）、更新 steps
- System prompt 要求 LLM 只返回 JSON: `{"evaluation": "sufficient"|"needs_more", "reason": "..."}`
- 如果 iteration >= max_iterations，直接设为 "sufficient"（强制退出循环）

**节点 D: `refine_query`**（仅 Agent 版使用）
- 输入：state.topic + state.queries + state.search_results（已有的查询和结果）
- 逻辑：调用 LLMService.chat()，让 LLM 根据已有结果生成一个新的、不同角度的搜索查询
- 输出：更新 queries（追加新查询）、更新 steps
- System prompt 要求：避免重复之前的查询，从不同角度切入

**节点 E: `generate_report`**
- 输入：state.topic + state.search_results
- 逻辑：调用 LLMService.chat()，让 LLM 基于所有搜索结果生成结构化研究报告
- 报告格式：标题 / 摘要 / 关键发现（编号列表）/ 信息来源 / 结论
- 输出：更新 report、更新 steps

**所有节点的共同要求**：
- 接收 state dict，返回 partial state update dict（LangGraph 的标准模式）
- 通过构造函数或闭包注入 LLMService 和 RAGService（不在节点函数体内创建）
- 每个节点执行后，往 steps 追加一条 trace 记录
- 异常处理：LLM 或 RAG 调用失败时，在 steps 中记录错误，不中断整个图的执行

### 4. Workflow 版 — `app/services/research/workflow.py`

构建确定性工作流（固定路径，不做动态决策）：

```python
# 图结构：
#   START → rewrite_query → search → generate_report → END
#
# 特征：
# - 只搜索一次
# - 不评估结果是否充分
# - 不做查询优化循环
# - 路径完全确定
#
# 实现：
# - 使用 langgraph.graph.StateGraph
# - add_node() 注册节点
# - add_edge() 连接固定边
# - compile() 生成可执行图
# - 提供 async def run_workflow(topic, max_iterations, settings, rag_service, llm_service) -> dict
#   返回 {"report": "...", "steps": [...], "queries": [...], "iterations_used": 1}
```

### 5. Agent 版 — `app/services/research/agent.py`

构建 LLM 驱动的研究 Agent（动态决策循环）：

```python
# 图结构：
#   START → rewrite_query → search → evaluate_results → [router]
#     ├─ "sufficient" → generate_report → END
#     └─ "needs_more" → refine_query → search → evaluate_results → [router] → ...
#
# 关键：router 函数
# - 读取 state["evaluation"]
# - 返回 "sufficient" 或 "needs_more"
# - 如果 state["iteration"] >= state["max_iterations"]，返回 "sufficient"（保底退出）
#
# 这就是 Conditional Edge：
#   graph.add_conditional_edges(
#       "evaluate_results",
#       router_function,
#       {"sufficient": "generate_report", "needs_more": "refine_query"}
#   )
#
# 实现：
# - 使用 langgraph.graph.StateGraph
# - add_node() 注册 5 个节点
# - add_edge() 连接固定边 (START → rewrite_query, rewrite_query → search, refine_query → search, search → evaluate, generate_report → END)
# - add_conditional_edges() 连接条件边 (evaluate_results → router → generate/refine)
# - compile() 生成可执行图
# - 提供 async def run_agent(topic, max_iterations, settings, rag_service, llm_service) -> dict
#   返回 {"report": "...", "steps": [...], "queries": [...], "iterations_used": N, "evaluation_history": [...]}
```

### 6. `app/services/research/__init__.py`

导出 `run_workflow` 和 `run_agent` 两个主函数。

### 7. Schemas — `app/schemas/research.py`

```python
# ResearchRequest:
#   topic: str                        — 研究主题（必填，最少 2 字符）
#   mode: Literal["workflow", "agent"] — 执行模式（必填）
#   max_iterations: int = 3           — Agent 模式最大搜索轮次（1-10）
#   top_k: int = 5                    — 每次搜索返回的结果数
#
# StepRecord:
#   node: str                         — 节点名
#   action: str                       — 执行的动作描述
#   output_summary: str               — 输出摘要（截断到 200 字符）
#   timestamp: str                    — ISO 格式时间戳
#
# ResearchResponse:
#   topic: str                        — 原始研究主题
#   mode: str                         — 执行模式
#   report: str                       — 研究报告
#   queries: list[str]                — 所有查询
#   steps: list[StepRecord]           — 完整 action trace
#   iterations_used: int              — 实际搜索轮次
#   search_result_count: int          — 搜索结果总数
```

### 8. 配置 — 扩展 `app/core/config.py`

新增（Tavily 配置在 Part A 已定义，此处只加 research 配置）：
```python
research_max_iterations: int = Field(default=3, ge=1, le=10)   # Agent 默认最大搜索轮次
research_top_k: int = Field(default=5, ge=1, le=20)            # 每次搜索的结果数
```

### 9. API 端点 — `app/api/routes/research.py`

```
POST /api/v1/research
```

请求体（ResearchRequest）：
```json
{
    "topic": "RAG 系统中 Chunking 策略对检索质量的影响",
    "mode": "agent",
    "max_iterations": 3,
    "top_k": 5
}
```

响应体（ResearchResponse）：
```json
{
    "topic": "RAG 系统中 Chunking 策略对检索质量的影响",
    "mode": "agent",
    "report": "# Chunking 策略与检索质量\n\n## 摘要\n...\n\n## 关键发现\n1. ...\n2. ...\n\n## 结论\n...",
    "queries": [
        "chunking strategy impact on RAG retrieval quality",
        "document splitting methods semantic search accuracy"
    ],
    "steps": [
        {"node": "rewrite_query", "action": "Rewrote topic to search query", "output_summary": "chunking strategy impact...", "timestamp": "2026-04-19T15:30:00"},
        {"node": "search_knowledge_base", "action": "Searched with query", "output_summary": "Found 5 results", "timestamp": "2026-04-19T15:30:02"},
        {"node": "evaluate_results", "action": "Evaluated search results", "output_summary": "needs_more: results lack detail on...", "timestamp": "2026-04-19T15:30:04"},
        {"node": "refine_query", "action": "Generated refined query", "output_summary": "document splitting methods...", "timestamp": "2026-04-19T15:30:06"},
        {"node": "search_knowledge_base", "action": "Searched with refined query", "output_summary": "Found 5 more results", "timestamp": "2026-04-19T15:30:08"},
        {"node": "evaluate_results", "action": "Evaluated search results", "output_summary": "sufficient: comprehensive coverage", "timestamp": "2026-04-19T15:30:10"},
        {"node": "generate_report", "action": "Generated research report", "output_summary": "Report generated (1234 chars)", "timestamp": "2026-04-19T15:30:15"}
    ],
    "iterations_used": 2,
    "search_result_count": 10
}
```

同时提供一个对比端点（可选）：

```
POST /api/v1/research/compare
```

同时运行 workflow 和 agent 版本，返回两个结果供对比：
```json
{
    "topic": "...",
    "workflow_result": { "...ResearchResponse..." },
    "agent_result": { "...ResearchResponse..." }
}
```

### 10. main.py 注册

在 `app/main.py` 中注册新 router：
```python
from app.api.routes.research import router as research_router
app.include_router(research_router)
```

### 11. 测试要求

在 `tests/` 下新增测试，覆盖：

- **test_research_nodes.py**: 每个节点函数的单元测试
  - rewrite_query: mock LLMService.chat()，验证查询被追加到 queries
  - search (多源): mock RAGService.search() + mock ToolRegistry.execute()，验证两源结果合并
  - search (RAG 失败): mock RAG 抛异常，验证 web 结果仍然返回
  - search (web 失败): mock web 抛异常，验证 RAG 结果仍然返回
  - search (无 Tavily key): 验证只用知识库搜索
  - evaluate_results: mock LLMService.chat()，验证 evaluation 被设置
  - evaluate_results 达到 max_iterations: 验证自动返回 "sufficient"
  - refine_query: mock LLMService.chat()，验证新查询被追加
  - generate_report: mock LLMService.chat()，验证 report 被设置
  - 节点异常处理：mock LLM 抛出异常，验证 steps 中记录错误且不崩溃

- **test_research_workflow.py**: Workflow 图的集成测试
  - 完整执行：mock LLM + RAG，验证图从 START 走到 END
  - 验证只搜索了 1 次（workflow 不循环）
  - 验证 steps 长度 = 3（rewrite → search → generate）
  - 验证输出结构（report 非空、queries 有 1 个）

- **test_research_agent.py**: Agent 图的集成测试
  - 首次搜索就充分：evaluate 返回 "sufficient" → 直接生成报告
  - 需要精炼一次：evaluate 先返回 "needs_more"，再返回 "sufficient"
  - 达到 max_iterations：验证强制退出循环并生成报告
  - 验证 steps 的完整性和顺序

- **test_research_endpoint.py**: API 端点测试
  - POST /api/v1/research (workflow mode): mock graph 执行，验证响应格式
  - POST /api/v1/research (agent mode): mock graph 执行，验证响应格式
  - 无效 mode: 验证 422
  - topic 为空: 验证 422
  - max_iterations 超范围: 验证 422

所有测试使用 mock，不调用真实 LLM API 或 Qdrant。

## 实现顺序建议

**Part A（新工具）**：
1. `app/core/config.py` — 新增 tavily_api_key、tavily_base_url 配置项
2. `app/services/tools/web_search.py` — Tavily Web Search 工具
3. `app/services/tools/code_executor.py` — 沙箱代码执行工具
4. `app/services/tools/__init__.py` — 导出新工厂函数
5. `app/services/tool_registry.py` — 在 `_register_defaults()` 中注册两个新工具
6. `tests/test_tools_builtin.py` — 追加新工具的测试
7. 运行 `python -m pytest -v` — 确保所有 103+ 旧测试仍通过

**Part B（研究助理 Workflow & Agent）**：
8. `requirements.txt` — 添加 langgraph，然后 `pip install langgraph`
9. `app/core/config.py` — 新增 research_* 配置项
10. `app/schemas/research.py` — 数据模型
11. `app/services/research/state.py` — ResearchState TypedDict
12. `app/services/research/nodes.py` — 5 个节点函数
13. `app/services/research/workflow.py` — Workflow 图
14. `app/services/research/agent.py` — Agent 图
15. `app/services/research/__init__.py` — 导出
16. `app/api/routes/research.py` — API 端点
17. `app/main.py` — 注册 router
18. `tests/` — 全部研究助理测试
19. 运行 `python -m pytest -v` 确保全部通过

## 代码规范

- 遵循现有代码风格：类型注解、async/await、依赖注入
- **LangGraph 节点函数应是纯函数（或闭包）**，接收 state 返回 partial update
- 通过工厂函数或闭包将 LLMService / RAGService 注入节点，**不要在节点函数体内直接实例化 service**
- 保持服务层可测试：mock LLMService 和 RAGService 即可测试所有节点和图
- 错误处理：节点内部的 LLM/RAG 调用异常不应让整个图崩溃，应被捕获并记录到 steps
- 不要修改现有测试（Phase 3 及之前的 103 个测试必须继续通过）
- 使用 `from __future__ import annotations` 保持类型注解一致

## 设计哲学

**Workflow vs Agent 的核心区别体现在 "边" 上**：
- Workflow: 所有边都是 `add_edge()`（固定）
- Agent: 关键位置使用 `add_conditional_edges()`（LLM 决定走哪条路）

两个版本 **共享完全相同的节点函数**。区别仅在于图的连接方式。这就是 Phase 4 要传达的核心洞见。

**Anthropic 的关键原则**：
> "在大多数场景下，Workflow 比 Agent 更适合生产环境。Agent 是最后的选择，不是第一选择。"

通过实现和对比两个版本，学习者能直观感受：
- Workflow 更快、更可预测、更易调试
- Agent 更灵活、能处理不确定性、但成本更高
- 应根据任务需求选择，而非默认用 Agent

## 完成标准

**Part A（新工具）**：
- [ ] `web_search` 工具通过 httpx 调用 Tavily REST API，返回格式化搜索结果
- [ ] `execute_python` 工具在独立子进程中执行代码，有超时和关键词黑名单保护
- [ ] 两个新工具在 ToolRegistry 注册，`GET /api/v1/tools/list` 能看到 5 个工具
- [ ] `POST /api/v1/tools/chat` 能使用新工具（如 "搜索最新的AI新闻"）
- [ ] 新工具测试全部通过

**Part B（研究助理）**：
- [ ] LangGraph StateGraph 能正常编译和执行
- [ ] Workflow 版：固定 3 步（rewrite → search → report），执行路径确定
- [ ] Agent 版：LLM 动态决策循环（search → evaluate → refine/report），支持多轮搜索
- [ ] search 节点并行执行 RAG + Web 搜索，任一失败不阻塞另一个
- [ ] Agent 的 max_iterations 能正确限制循环次数
- [ ] 条件路由正确工作（evaluate_results 的结果决定下一个节点）
- [ ] 5 个节点函数正确实现，可被两个图共享
- [ ] Action trace 完整记录每个步骤
- [ ] 所有新测试通过
- [ ] 所有 103 个旧测试仍然通过
- [ ] `POST /api/v1/research` 能接收 mode 参数选择 workflow/agent
- [ ] 节点异常不导致整个图崩溃

## 关于 LangGraph 版本兼容性

如果在实现过程中遇到 LangGraph API 变化（不同版本的方法签名可能不同），以实际安装版本的 API 为准。核心概念不变：
- `StateGraph(state_schema)` 创建图
- `.add_node(name, function)` 添加节点
- `.add_edge(from, to)` 添加固定边
- `.add_conditional_edges(from, router_fn, mapping)` 添加条件边
- `.compile()` 编译图
- 编译后的图用 `.ainvoke(initial_state)` 异步执行

如果某个 API 在安装版本中不存在，查阅安装版本的文档或源码寻找替代方案，而非硬编码过时的 API。

# Phase 5: Memory / Planning / Reflection & Multi-Agent — Claude Code 实现 Prompt

## 项目背景

这是一个 AI Agent 8 周学习项目，使用 FastAPI 后端。当前已完成：

- **Phase 0**: Python 工程基础 — 项目脚手架、FastAPI 服务、Settings (pydantic-settings)、pytest
- **Phase 1**: LLM 基础 — 通用 /chat 端点、/extract 端点、Prompt Service
- **Phase 2**: RAG 系统 — 文档解析 (docling)、分块、embedding (text-embedding-3-large, 3072 dim)、Qdrant 向量检索、Cohere rerank、/rag/ingest + /rag/search + /rag/ask 端点
- **Phase 3**: Tool Use — 工具注册表、5 个内置工具 (get_current_time / calculate / search_knowledge_base / web_search / execute_python)、Tool Calling Loop、/tools/chat + /tools/list 端点
- **Phase 4**: Workflow & Agent — LangGraph StateGraph 编排、Workflow 模式（确定性 3 步）、Agent 模式（LLM 驱动循环 search → evaluate → refine/report）、多源并行搜索（RAG + Web via asyncio.gather）、/api/v1/research 端点

## 技术栈约束

| 依赖 | 版本 | 备注 |
|------|------|------|
| Python | 3.11 | conda env `ai-agent` |
| FastAPI | 0.115.0 | |
| pydantic | 2.9.2 | |
| pydantic-settings | 2.5.2 | |
| httpx | 0.27.2 | **唯一 HTTP 客户端，禁止引入 openai SDK、langchain-openai 或 requests** |
| pytest | 8.3.3 | pytest-asyncio, asyncio_mode=auto |
| langgraph | >=0.2.0 | 已安装 (0.6.11)，仅用于图编排，不使用 langchain 的 LLM 封装 |

**LLM 提供商**: xairouter (`https://api.xairouter.com/v1`)，兼容 OpenAI chat/completions 格式，模型 `gpt-5.4`。

**关键约束**:
- 所有 LLM 调用仍然通过现有的 `LLMService`（httpx），**不引入 langchain-openai / ChatOpenAI 等 LLM 封装**
- LangGraph 仅用于状态图编排（StateGraph、节点、边、条件路由）
- 保持现有项目分层架构: `app/core/`, `app/schemas/`, `app/services/`, `app/api/routes/`
- 新代码需要配套 pytest 单元测试（mock 外部 API 调用）
- 不要修改现有测试（Phase 4 及之前的 135 个测试必须继续通过）
- 使用 `from __future__ import annotations` 保持类型注解一致

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
│   │   ├── research.py                 # ResearchRequest/Response, StepRecord
│   │   └── tools.py                    # ToolChatRequest/Response, ToolInfo
│   ├── services/
│   │   ├── llm_service.py              # LLMService.chat(), .extract(), .chat_with_tools()
│   │   ├── prompt_service.py           # 系统提示词常量
│   │   ├── tool_registry.py            # ToolRegistry — 工具注册/执行
│   │   ├── tools/                      # 5 个内置工具
│   │   │   ├── __init__.py
│   │   │   ├── get_current_time.py
│   │   │   ├── calculate.py
│   │   │   ├── search_knowledge_base.py
│   │   │   ├── web_search.py
│   │   │   └── code_executor.py
│   │   ├── research/                   # Phase 4 研究助理模块
│   │   │   ├── __init__.py             # 导出 run_workflow, run_agent
│   │   │   ├── state.py                # ResearchState TypedDict
│   │   │   ├── nodes.py                # 5 个节点工厂函数
│   │   │   ├── workflow.py             # 确定性工作流图
│   │   │   └── agent.py                # LLM 驱动 Agent 图
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
│       ├── tools.py                    # /api/v1/tools/chat, /api/v1/tools/list
│       └── research.py                 # /api/v1/research
├── tests/                              # 135 个通过的 pytest 测试
├── requirements.txt
├── pytest.ini                          # asyncio_mode = auto
└── .env
```

**已有的关键 Service 接口（Phase 5 需要复用）**：

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

# ToolRegistry（app/services/tool_registry.py）
class ToolRegistry:
    def __init__(self, settings: Settings): ...
    async def execute(self, tool_name: str, arguments: dict) -> ToolCallRecord: ...
    def list_tools(self) -> list[dict]: ...
    settings: Settings  # 可访问配置
```

**Phase 4 已有的研究状态定义**：

```python
# app/services/research/state.py（当前完整内容）
class ResearchSearchResult(TypedDict):
    source: str           # "knowledge_base" | "web"
    query: str
    text_snippet: str
    score: float
    title: str
    url: str | None

class ResearchStep(TypedDict):
    node: str
    action: str
    output_summary: str
    timestamp: str

class ResearchState(TypedDict):
    topic: str
    queries: Annotated[list[str], operator.add]          # 追加语义
    search_results: Annotated[list[ResearchSearchResult], operator.add]  # 追加语义
    report: str
    steps: Annotated[list[ResearchStep], operator.add]   # 追加语义
    iteration: int
    max_iterations: int
    evaluation: str                                       # "sufficient" | "needs_more"
    top_k: int
```

**Phase 4 已有的 5 个节点函数**（app/services/research/nodes.py）:

| 工厂函数 | 节点 | 作用 |
|----------|------|------|
| `make_rewrite_query_node(llm)` | rewrite_query | LLM 重写 topic 为优化查询 |
| `make_search_node(rag, registry)` | search | 并行 RAG + Web 搜索（asyncio.gather） |
| `make_evaluate_results_node(llm)` | evaluate_results | LLM 判断结果是否充分 |
| `make_refine_query_node(llm)` | refine_query | LLM 生成新角度查询 |
| `make_generate_report_node(llm)` | generate_report | LLM 生成结构化报告 |

**Phase 4 已有的两个图**:
- **Workflow**: START → rewrite_query → search → generate_report → END（固定路径，搜索 1 次）
- **Agent**: START → rewrite_query → search → evaluate_results → [conditional: sufficient → generate_report → END | needs_more → refine_query → search → …]

**Phase 4 缺失（Phase 5 要补齐的能力）**：
- ❌ Memory 系统（短期/长期/工作记忆）— 当前无任何记忆机制
- ❌ Planning（任务分解）— 当前直接搜索，无分步计划
- ❌ Reflection（自我批评与修正）— 当前 evaluate_results 只做 sufficient/needs_more 二分判断
- ❌ Multi-Agent 协作 — 当前是单 Agent 图
- ❌ 会话持久化 — 当前每次请求独立，无跨请求状态

---

## Phase 5 目标

Phase 5 有三大任务，将基础研究助理升级为"具有记忆、规划和自我修正能力的多角色协作智能体系统"：

1. **Part A: Memory 系统** — 为 Agent 增加短期记忆（会话历史）、长期记忆（跨会话持久化洞见）和工作记忆（增强的任务状态）
2. **Part B: Planning & Reflection** — 增加 plan 节点（任务分解）和 reflect 节点（报告质量自检与修正），升级 Agent 循环
3. **Part C: Multi-Agent 协作** — 实现 Supervisor 架构，将单体 Agent 拆分为 Planner / Researcher / Writer / Reviewer 四个专业角色

### 对应学习路线要求

**来自 roadmap Phase 5（多 Agent / Memory / Planning）**:
> - 核心知识点: multi-agent 适用边界, role-based collaboration, planning / routing / reflection / critique, semantic / episodic / short-term memory
> - 推荐顺序: 先 planning + reflection，再多 Agent
> - 阶段产出物: 多 Agent 版本, memory 设计说明
> - 完成标准: 能说明多 Agent 的收益与成本

**来自学习方案 Phase 5（单 Agent 系统设计）**:
> - Agent 核心循环: Perceive → Plan → Act → Observe
> - ReAct 模式
> - Planning 策略: Task Decomposition / Plan-and-Solve
> - Memory 系统: 短期记忆/长期记忆/语义记忆
> - Reflection 与自纠错
> - Agent 的失败模式与处理

**来自学习方案 Part D 里程碑 5+6**:
> - 里程碑 5: ReAct 模式的研究 Agent, Memory 系统（跨会话记忆）, Planning（自动拆解研究任务）, Reflection（自我检查和修正）, 失败处理和重试
> - 里程碑 6: Searcher Agent + Analyst Agent + Writer Agent + Reviewer Agent, Supervisor 编排多 Agent 协作

---

## Part A: Memory 系统

### A1. Memory 架构设计

Phase 5 引入三层记忆：

| 记忆类型 | 存储位置 | 生命周期 | 作用 |
|----------|----------|----------|------|
| **短期记忆 (Short-term)** | 内存 dict | 单个会话（session） | 同一 session_id 的连续研究请求共享上下文 |
| **工作记忆 (Working)** | ResearchState 扩展字段 | 单次图执行 | 当前任务的计划、子任务状态、反思笔记 |
| **长期记忆 (Long-term)** | JSON 文件持久化 | 跨会话永久 | 保存研究洞见（insights），后续研究可检索利用 |

**设计原则**:
- 教学级实现，不引入 Redis/PostgreSQL 等新外部依赖
- 短期记忆用 Python dict（进程内），长期记忆用 JSON 文件
- 记忆读写规则清晰：什么时候写入、什么时候读取、什么时候过期
- Memory 是可选增强，不破坏现有的 workflow/agent 模式

### A2. Memory Service — `app/services/memory_service.py`（新增）

```python
# MemoryService 负责管理三层记忆
# 
# 短期记忆（会话级）:
#   - 存储结构: dict[str, SessionMemory]
#     key = session_id (str)
#     value = SessionMemory(TypedDict):
#       session_id: str
#       created_at: str             # ISO timestamp
#       last_accessed: str          # ISO timestamp
#       topics: list[str]           # 本会话研究过的主题
#       insights: list[str]         # 本会话积累的关键发现
#       total_queries: int          # 本会话总查询次数
#
#   - add_session_context(session_id, topic, insights): 添加上下文
#   - get_session_context(session_id) -> SessionMemory | None: 获取上下文
#   - clear_session(session_id): 清除会话
#
# 长期记忆（持久化）:
#   - 存储位置: data/memory/long_term.json（自动创建目录）
#   - 存储结构: list[InsightRecord]
#     InsightRecord(TypedDict):
#       topic: str                  # 研究主题
#       insight: str                # 关键洞见（一句话总结）
#       source_count: int           # 基于多少条搜索结果得出
#       created_at: str             # ISO timestamp
#       session_id: str             # 来自哪个会话
#
#   - save_insight(topic, insight, source_count, session_id): 保存洞见
#   - retrieve_relevant_insights(query, top_k=3) -> list[InsightRecord]:
#       简单文本匹配检索（用关键词 overlap 打分，不用向量搜索）
#       这是教学级实现，生产环境应使用向量存储
#   - get_all_insights() -> list[InsightRecord]: 获取全部洞见
#
# 初始化:
#   - __init__(self, data_dir: str = "data/memory"): 指定数据目录
#   - 启动时自动从 JSON 文件加载长期记忆
#   - 短期记忆从空 dict 开始（进程重启后丢失，这是设计选择）
#
# 线程安全:
#   - 使用 asyncio.Lock 保护 JSON 文件读写
#   - 短期记忆 dict 在同一 event loop 内无竞争问题
```

### A3. 扩展 ResearchState — 修改 `app/services/research/state.py`

在现有 ResearchState 基础上新增工作记忆字段：

```python
# 新增字段（追加到现有 ResearchState，不删除任何现有字段）:
#
# plan: list[str]                     # 任务分解产生的子任务列表
#   - 默认空列表
#   - 不使用 operator.add（覆盖语义，plan 节点整体替换）
#
# current_step: str                   # 当前正在执行的计划步骤
#   - 默认空字符串
#
# reflection: str                     # reflect 节点的质量评估
#   - 默认空字符串
#   - "pass" 表示质量通过，其他值表示需要修改建议
#
# session_id: str                     # 当前会话 ID
#   - 默认空字符串
#   - 用于关联 MemoryService
#
# prior_insights: list[str]           # 从长期记忆检索到的相关洞见
#   - 默认空列表
#   - 不使用 operator.add（覆盖语义）
#
# 重要: 所有新字段都有默认值或是可选的，
# 保证现有 workflow/agent 的 initial state 不需要修改也能正常工作。
# 即现有 Phase 4 的 run_workflow() 和 run_agent() 不传这些字段时，
# LangGraph 应使用默认值。如果 LangGraph TypedDict 不支持默认值，
# 在 run_workflow/run_agent 的 initial state 中补上这些字段即可。
```

### A4. 配置 — 扩展 `app/core/config.py`

新增：
```python
# Memory 配置
memory_data_dir: str = "data/memory"         # 长期记忆存储目录
memory_max_insights: int = Field(default=100, ge=10, le=1000)  # 长期记忆最大洞见数
memory_session_ttl: int = Field(default=3600, ge=60)           # 短期记忆会话过期时间（秒）
```

---

## Part B: Planning & Reflection

### B1. 核心概念

**Planning（任务分解）**:
- Phase 4 的 Agent 直接将 topic 重写为查询然后搜索。没有"想想该怎么研究这个问题"的步骤。
- Phase 5 增加 `plan` 节点：LLM 将研究主题分解为 2-4 个子问题/子任务，然后逐步搜索。
- 对应 Plan-and-Solve 模式：先计划，再执行。

**Reflection（自我批评）**:
- Phase 4 的 `evaluate_results` 只判断"结果够不够"（二分类），不检查报告质量。
- Phase 5 增加 `reflect` 节点：在 `generate_report` 之后、返回之前，LLM 审查报告质量，指出不足并给出修改建议。
- 如果质量不通过，触发报告修订循环（最多 1 次修订，避免死循环）。

### B2. 新增节点 — 修改 `app/services/research/nodes.py`

在现有 5 个节点基础上，新增 3 个节点工厂函数：

**节点 F: `make_plan_node(llm_service)` → `plan`**
```python
# 输入: state.topic + state.prior_insights
# 逻辑:
#   1. 如果有 prior_insights（从长期记忆检索到的相关洞见），包含在 prompt 中
#   2. 调用 LLMService.chat()，让 LLM 将研究主题分解为 2-4 个子问题
#   3. System prompt 要求返回 JSON: {"sub_tasks": ["问题1", "问题2", ...]}
#   4. 解析 JSON，提取 sub_tasks 列表
# 输出:
#   plan: list[str]              # 覆盖语义，整体替换
#   steps: [_step("plan", ...)]  # 追加语义
#
# 异常处理: 解析失败时，fallback 为单个子任务 [topic]
#
# System prompt 示例:
# "You are a research planner. Given a topic, break it down into 2-4 specific
#  sub-questions that together would comprehensively cover the topic.
#  Return JSON: {\"sub_tasks\": [\"question 1\", \"question 2\", ...]}"
```

**节点 G: `make_reflect_node(llm_service)` → `reflect`**
```python
# 输入: state.topic + state.report + state.search_results
# 逻辑:
#   1. 调用 LLMService.chat()，让 LLM 审查已生成的报告
#   2. 评估维度: 完整性、准确性、结构清晰度、是否有遗漏
#   3. System prompt 要求返回 JSON:
#      {"verdict": "pass"|"revise", "feedback": "...具体修改建议..."}
#   4. 如果 verdict == "pass"，设置 reflection = "pass"
#   5. 如果 verdict == "revise"，设置 reflection = feedback 内容
# 输出:
#   reflection: str              # "pass" 或修改建议文本
#   steps: [_step("reflect", ...)]
#
# 异常处理: 解析失败时 fallback 为 "pass"（不阻塞输出）
#
# System prompt 示例:
# "You are a research report reviewer. Evaluate the report for:
#  completeness, accuracy, clarity, and coverage of the topic.
#  Return JSON: {\"verdict\": \"pass\"|\"revise\", \"feedback\": \"...\"}"
```

**节点 H: `make_revise_report_node(llm_service)` → `revise_report`**
```python
# 输入: state.topic + state.report + state.reflection + state.search_results
# 逻辑:
#   1. 将原报告 + 修改建议 + 原始搜索结果一起提供给 LLM
#   2. 调用 LLMService.chat()，让 LLM 根据反馈修订报告
#   3. 返回修订后的报告
# 输出:
#   report: str                  # 覆盖语义，替换原报告
#   reflection: "pass"           # 修订后设为 pass，避免再次循环
#   steps: [_step("revise_report", ...)]
#
# System prompt 示例:
# "You are a research report editor. Revise the report based on the reviewer's feedback.
#  Keep the same structure, improve the identified weaknesses."
```

**节点 I: `make_recall_memory_node(memory_service)` → `recall_memory`**
```python
# 输入: state.topic + state.session_id
# 逻辑:
#   1. 从 MemoryService 检索与 topic 相关的长期记忆洞见
#   2. 从 MemoryService 获取当前 session 的上下文
#   3. 将检索到的洞见放入 state.prior_insights
# 输出:
#   prior_insights: list[str]    # 覆盖语义
#   steps: [_step("recall_memory", ...)]
#
# 此节点不调用 LLM，只访问 MemoryService
```

**节点 J: `make_save_memory_node(memory_service)` → `save_memory`**
```python
# 输入: state.topic + state.report + state.search_results + state.session_id
# 逻辑:
#   1. 从报告中提取关键洞见（取报告前 200 字符作为 insight 摘要）
#   2. 保存到 MemoryService 长期记忆
#   3. 更新 session 上下文（topics, insights, total_queries）
# 输出:
#   steps: [_step("save_memory", ...)]
#
# 此节点不调用 LLM，只访问 MemoryService
```

### B3. 升级 Agent 图 — 新增 `app/services/research/agent_v2.py`

创建增强版 Agent 图（保留原 agent.py 不修改）：

```python
# 图结构 (agent_v2):
#
#   START → recall_memory → plan → rewrite_query → search → evaluate_results → [router_eval]
#     ├─ "sufficient" → generate_report → reflect → [router_reflect]
#     │                                    ├─ "pass" → save_memory → END
#     │                                    └─ "revise" → revise_report → save_memory → END
#     └─ "needs_more" → refine_query → search → evaluate_results → [router_eval] → ...
#
# 与 Phase 4 Agent 的区别:
#   1. 新增 recall_memory 节点（图入口，在 rewrite_query 之前）
#   2. 新增 plan 节点（在 rewrite_query 之前，recall_memory 之后）
#   3. rewrite_query 现在可以参考 plan 中的子任务
#   4. 新增 reflect 节点（在 generate_report 之后）
#   5. 新增 revise_report 节点（reflect 判定需要修改时）
#   6. 新增 save_memory 节点（图出口，在 END 之前）
#   7. 两个条件路由: router_eval（同 Phase 4）+ router_reflect（新增）
#
# 条件路由函数:
#   _route_after_evaluation(state):  # 复用 Phase 4 逻辑
#     iteration >= max_iterations → "sufficient"
#     evaluation == "sufficient" → "sufficient"
#     否则 → "needs_more"
#
#   _route_after_reflection(state):  # 新增
#     reflection == "pass" → "pass"
#     否则 → "revise"
#
# 函数签名:
# async def run_agent_v2(
#     topic: str,
#     max_iterations: int,
#     top_k: int,
#     rag_service: RAGService,
#     llm_service: LLMService,
#     tool_registry: ToolRegistry,
#     memory_service: MemoryService,
#     session_id: str = "",
# ) -> dict[str, Any]:
#
# initial state 扩展（在 Phase 4 基础上新增）:
#   plan: []
#   current_step: ""
#   reflection: ""
#   session_id: session_id
#   prior_insights: []
#
# 返回值扩展（在 Phase 4 基础上新增）:
#   plan: list[str]              # 任务分解列表
#   reflection_history: str      # 反思结果
#   insights_used: int           # 使用了多少条历史洞见
```

### B4. 不修改现有图

- `app/services/research/workflow.py`（run_workflow）— **不修改**
- `app/services/research/agent.py`（run_agent）— **不修改**
- 两个旧图继续工作，保证 Phase 4 测试不受影响
- 新增 `agent_v2.py`（run_agent_v2）作为增强版

---

## Part C: Multi-Agent 协作

### C1. Multi-Agent 架构设计

实现 **Supervisor 模式**的多 Agent 协作系统。Supervisor 负责协调 4 个专业角色：

```
                    ┌───────────────┐
                    │  Supervisor   │
                    │  (协调分发)    │
                    └───────┬───────┘
              ┌─────────┬───┴───┬──────────┐
              ↓         ↓       ↓          ↓
        ┌──────────┐ ┌──────┐ ┌──────┐ ┌──────────┐
        │Researcher│ │Analyst│ │Writer│ │Reviewer  │
        │(搜索专家) │ │(分析) │ │(撰写) │ │(质量审核) │
        └──────────┘ └──────┘ └──────┘ └──────────┘
```

**角色职责**:

| 角色 | 核心职责 | 使用的工具/服务 | 输出 |
|------|----------|----------------|------|
| **Supervisor** | 接收主题、分配任务、汇总结果、决定流程 | LLMService | 任务分配指令 |
| **Researcher** | 执行多源搜索（RAG + Web） | RAGService, ToolRegistry | search_results |
| **Analyst** | 分析搜索结果，提取关键发现，评估信息充足度 | LLMService | analysis, evaluation |
| **Writer** | 基于分析结果撰写结构化研究报告 | LLMService | report |
| **Reviewer** | 审查报告质量，给出修改意见或通过 | LLMService | review verdict |

### C2. Multi-Agent State — `app/services/multi_agent/state.py`（新增）

```python
# MultiAgentState TypedDict:
#
# 共享字段（所有角色可读写）:
#   topic: str                      # 研究主题
#   search_results: Annotated[list[ResearchSearchResult], operator.add]
#   report: str
#   steps: Annotated[list[ResearchStep], operator.add]   # 追踪所有角色的行动
#
# Supervisor 专属:
#   plan: list[str]                 # 子任务列表（覆盖语义）
#   current_phase: str              # "research" | "analysis" | "writing" | "review" | "done"
#   iteration: int                  # 研究迭代轮次
#   max_iterations: int
#   top_k: int
#
# Analyst 专属:
#   analysis: str                   # 分析结果文本
#   evaluation: str                 # "sufficient" | "needs_more"
#
# Reviewer 专属:
#   review_verdict: str             # "approved" | "needs_revision"
#   review_feedback: str            # 修改建议
#
# Memory 集成:
#   session_id: str
#   prior_insights: list[str]
#
# 复用 ResearchSearchResult 和 ResearchStep 类型（从 research/state.py 导入）
```

### C3. Multi-Agent 角色节点 — `app/services/multi_agent/roles.py`（新增）

```python
# 4 个角色节点工厂函数 + 1 个 supervisor 路由:
#
# --- Researcher ---
# make_researcher_node(rag_service, tool_registry) → NodeHandler
#   - 与 Phase 4 的 search 节点逻辑基本相同
#   - 并行 RAG + Web 搜索
#   - 输出: search_results, steps
#
# --- Analyst ---
# make_analyst_node(llm_service) → NodeHandler
#   - 分析搜索结果，提取关键发现
#   - 判断信息是否充足
#   - System prompt: "You are a research analyst. Analyze the search results...
#     Return JSON: {\"analysis\": \"...\", \"evaluation\": \"sufficient\"|\"needs_more\",
#     \"key_findings\": [\"...\"]}"
#   - 输出: analysis, evaluation, steps
#
# --- Writer ---
# make_writer_node(llm_service) → NodeHandler
#   - 基于 analysis 和 search_results 撰写报告
#   - 使用增强的 system prompt，要求更高质量的结构化输出
#   - System prompt: "You are a professional research writer. Based on the analysis
#     and evidence, write a comprehensive research report with: Title, Executive Summary,
#     Key Findings (numbered), Methodology Notes, Sources, Conclusion."
#   - 输出: report, steps
#
# --- Reviewer ---
# make_reviewer_node(llm_service) → NodeHandler
#   - 审查 report 质量
#   - 与 reflect 节点类似，但更注重多角度审查
#   - System prompt: "You are a senior research reviewer. Evaluate the report...
#     Return JSON: {\"verdict\": \"approved\"|\"needs_revision\", \"feedback\": \"...\"}"
#   - 输出: review_verdict, review_feedback, steps
#
# --- Supervisor 路由函数（不是节点，是条件路由器）---
# _route_supervisor(state) → str:
#   if current_phase == "research":
#     return "researcher"
#   if current_phase == "analysis":
#     return "analyst"
#   if current_phase == "writing":
#     return "writer"
#   if current_phase == "review":
#     return "reviewer"
#   return "done"
#
# 注意: Supervisor 的路由逻辑嵌入到图的 conditional_edges 中，
# 不需要单独的 Supervisor 节点。流程推进由 transition 节点负责。
```

### C4. Multi-Agent 图 — `app/services/multi_agent/graph.py`（新增）

```python
# 图结构 (multi-agent):
#
#   START → plan_research → researcher → analyst → [route_after_analysis]
#     ├─ "sufficient" → writer → reviewer → [route_after_review]
#     │                                       ├─ "approved" → END
#     │                                       └─ "needs_revision" → writer → reviewer → ...
#     └─ "needs_more" → refine_query → researcher → analyst → [route_after_analysis] → ...
#
# 节点清单（7 个）:
#   plan_research: LLM 分解研究任务（复用/改写 plan 节点）
#   researcher: 执行搜索（复用 search 节点逻辑）
#   analyst: 分析搜索结果 + 判断充足度
#   writer: 撰写报告
#   reviewer: 审查报告
#   refine_query: 优化搜索查询（复用 Phase 4 节点逻辑）
#
# 条件路由（2 个）:
#   route_after_analysis: evaluation → "sufficient" | "needs_more"
#     - iteration >= max_iterations → "sufficient"（保底退出）
#   route_after_review: review_verdict → "approved" | "needs_revision"
#     - 最多修订 1 次，防止死循环（用 iteration 或新字段 revision_count 跟踪）
#
# 函数签名:
# async def run_multi_agent(
#     topic: str,
#     max_iterations: int,
#     top_k: int,
#     rag_service: RAGService,
#     llm_service: LLMService,
#     tool_registry: ToolRegistry,
#     memory_service: MemoryService | None = None,
#     session_id: str = "",
# ) -> dict[str, Any]:
#
# 返回:
#   report: str
#   steps: list[dict]            # 完整 action trace，含每个角色的动作
#   queries: list[str]
#   iterations_used: int
#   search_result_count: int
#   plan: list[str]
#   analysis: str
#   review_verdict: str
#   agents_involved: list[str]   # ["planner", "researcher", "analyst", "writer", "reviewer"]
```

### C5. `app/services/multi_agent/__init__.py`（新增）

导出 `run_multi_agent`。

---

## 端点与 Schema 更新

### D1. 扩展 Schema — 修改 `app/schemas/research.py`

```python
# 修改 ResearchRequest，新增 mode 选项:
#   mode: Literal["workflow", "agent", "agent_v2", "multi_agent"]
#     - "workflow": Phase 4 确定性工作流（不变）
#     - "agent": Phase 4 基础 Agent（不变）
#     - "agent_v2": Phase 5 增强版单 Agent（+memory/planning/reflection）
#     - "multi_agent": Phase 5 多角色协作
#
# 新增可选字段:
#   session_id: str = ""         # 会话 ID，用于 memory 关联
#                                 # 空字符串表示不使用 memory
#
# 扩展 ResearchResponse，新增可选字段:
#   plan: list[str] = []         # 任务分解（agent_v2 / multi_agent 才有）
#   analysis: str = ""           # 分析结果（multi_agent 才有）
#   review_verdict: str = ""     # 审查结果（multi_agent 才有）
#   insights_used: int = 0       # 使用的历史洞见数
#   agents_involved: list[str] = []  # 参与的角色列表（multi_agent 才有）
```

### D2. 扩展 API 端点 — 修改 `app/api/routes/research.py`

```python
# POST /api/v1/research — 修改现有端点
#
# 新增 mode 分支:
#   mode == "workflow" → run_workflow() (不变)
#   mode == "agent" → run_agent() (不变)
#   mode == "agent_v2" → run_agent_v2() (新增)
#   mode == "multi_agent" → run_multi_agent() (新增)
#
# 当 mode 为 agent_v2 或 multi_agent 时:
#   - 创建 MemoryService 实例（模块级单例或路由依赖注入）
#   - 传入 session_id 参数
#
# 不修改 mode == "workflow" 和 mode == "agent" 的逻辑
```

### D3. 新增 Memory 端点 — `app/api/routes/memory.py`（新增）

```python
# 提供 Memory 管理 API（可选但推荐，便于调试和验证）:
#
# GET /api/v1/memory/insights
#   - 返回所有长期记忆洞见
#   - 响应: {"insights": [InsightRecord, ...], "total": int}
#
# GET /api/v1/memory/insights/search?query=xxx
#   - 搜索相关洞见
#   - 响应: {"insights": [InsightRecord, ...], "query": str}
#
# GET /api/v1/memory/sessions/{session_id}
#   - 返回指定会话的短期记忆
#   - 响应: SessionMemory | 404
#
# DELETE /api/v1/memory/sessions/{session_id}
#   - 清除指定会话的短期记忆
#   - 响应: {"status": "cleared"}
#
# DELETE /api/v1/memory/insights
#   - 清除所有长期记忆（危险操作，需确认）
#   - 响应: {"status": "cleared", "deleted_count": int}
```

### D4. main.py 注册

在 `app/main.py` 中注册新 router：
```python
from app.api.routes.memory import router as memory_router
app.include_router(memory_router)
```

---

## 实现顺序建议

按照学习路线推荐的顺序："先 planning + reflection，再多 Agent"。

**阶段 1: Memory 基础设施**
1. `app/core/config.py` — 新增 memory_* 配置项
2. `app/services/memory_service.py` — 实现 MemoryService
3. `tests/test_memory_service.py` — MemoryService 单元测试
4. 运行 `python -m pytest -v` — 确保 135 旧测试 + 新测试全通过

**阶段 2: 扩展状态与新节点**
5. `app/services/research/state.py` — 扩展 ResearchState 新字段
6. `app/services/research/nodes.py` — 新增 5 个节点工厂函数（plan, reflect, revise_report, recall_memory, save_memory）
7. `tests/test_research_nodes.py` — 追加新节点的测试
8. 运行 `python -m pytest -v`

**阶段 3: 增强版单 Agent (agent_v2)**
9. `app/services/research/agent_v2.py` — 增强版 Agent 图
10. `app/services/research/__init__.py` — 导出 run_agent_v2
11. `tests/test_research_agent_v2.py` — agent_v2 集成测试
12. 运行 `python -m pytest -v`

**阶段 4: Multi-Agent 协作**
13. `app/services/multi_agent/state.py` — MultiAgentState
14. `app/services/multi_agent/roles.py` — 4 个角色节点
15. `app/services/multi_agent/graph.py` — Multi-Agent 图
16. `app/services/multi_agent/__init__.py` — 导出
17. `tests/test_multi_agent_roles.py` — 角色节点单元测试
18. `tests/test_multi_agent_graph.py` — Multi-Agent 图集成测试
19. 运行 `python -m pytest -v`

**阶段 5: API 集成**
20. `app/schemas/research.py` — 扩展 mode 和响应字段
21. `app/api/routes/research.py` — 新增 agent_v2 / multi_agent 分支
22. `app/api/routes/memory.py` — Memory 管理端点
23. `app/main.py` — 注册 memory router
24. `tests/test_research_endpoint.py` — 追加 agent_v2 / multi_agent 端点测试
25. `tests/test_memory_endpoint.py` — Memory 端点测试
26. 运行 `python -m pytest -v` — 确保全部通过

---

## 测试要求

### 新增测试文件与覆盖范围

**`tests/test_memory_service.py`**（新增）:
- `test_save_and_retrieve_insight`: 保存洞见后能检索到
- `test_retrieve_relevant_insights`: 关键词匹配返回相关洞见
- `test_retrieve_no_match`: 无匹配时返回空列表
- `test_session_memory_add_and_get`: 添加会话上下文后能获取
- `test_session_memory_clear`: 清除会话后返回 None
- `test_long_term_persistence`: 保存到文件后，新实例能加载（需要临时目录）
- `test_max_insights_limit`: 超过上限时丢弃最旧的

**`tests/test_research_nodes.py`**（追加到现有文件）:
- `test_plan_node_success`: mock LLM 返回子任务列表
- `test_plan_node_with_insights`: 带 prior_insights 的规划
- `test_plan_node_parse_failure`: JSON 解析失败时 fallback
- `test_reflect_node_pass`: mock LLM 返回 "pass"
- `test_reflect_node_revise`: mock LLM 返回 "revise" + feedback
- `test_revise_report_node`: mock LLM 返回修订报告
- `test_recall_memory_node`: mock MemoryService，验证 prior_insights 被设置
- `test_save_memory_node`: mock MemoryService，验证 save_insight 被调用

**`tests/test_research_agent_v2.py`**（新增）:
- `test_agent_v2_full_pass`: plan → search → evaluate(sufficient) → report → reflect(pass) → save → END
- `test_agent_v2_reflect_revise`: 报告被 reflect 要求修订一次
- `test_agent_v2_with_memory`: 传入 session_id，验证 recall/save 节点执行
- `test_agent_v2_without_memory`: 空 session_id，验证 memory 节点优雅跳过
- `test_agent_v2_max_iterations`: 验证迭代上限强制退出

**`tests/test_multi_agent_roles.py`**（新增）:
- `test_researcher_node`: mock RAG + Web，验证搜索结果
- `test_analyst_node_sufficient`: mock LLM 返回 sufficient
- `test_analyst_node_needs_more`: mock LLM 返回 needs_more
- `test_writer_node`: mock LLM 生成报告
- `test_reviewer_node_approved`: mock LLM 返回 approved
- `test_reviewer_node_needs_revision`: mock LLM 返回 needs_revision + feedback

**`tests/test_multi_agent_graph.py`**（新增）:
- `test_multi_agent_full_path`: plan → research → analyze(sufficient) → write → review(approved) → END
- `test_multi_agent_needs_more_research`: analyze 返回 needs_more → 再搜索一次
- `test_multi_agent_revision`: review 返回 needs_revision → 修订一次
- `test_multi_agent_max_iterations`: 验证迭代上限

**`tests/test_research_endpoint.py`**（追加到现有文件）:
- `test_research_agent_v2_mode`: POST mode="agent_v2"，验证响应格式
- `test_research_multi_agent_mode`: POST mode="multi_agent"，验证响应格式
- `test_research_agent_v2_with_session`: 带 session_id 的请求

**`tests/test_memory_endpoint.py`**（新增）:
- `test_get_insights_empty`: 无洞见时返回空列表
- `test_get_insights_after_save`: 保存后能获取
- `test_search_insights`: 关键词搜索
- `test_get_session`: 获取会话信息
- `test_get_session_not_found`: 不存在的 session 返回 404
- `test_clear_session`: 清除会话
- `test_clear_all_insights`: 清除所有洞见

所有测试使用 mock，不调用真实 LLM API 或 Qdrant。Memory 测试使用 `tmp_path` fixture 提供临时目录。

---

## 代码规范

- 遵循现有代码风格：类型注解、async/await、依赖注入（闭包/工厂函数）
- LangGraph 节点函数是纯函数或闭包，接收 state 返回 partial update
- 通过工厂函数将 LLMService / RAGService / MemoryService 注入节点
- 节点内部异常不导致整个图崩溃，被捕获并记录到 steps
- 新增文件使用 `from __future__ import annotations`
- **不修改 Phase 4 及之前的任何测试文件**
- **不修改 workflow.py 和 agent.py**（保证向后兼容）
- MemoryService 的 JSON 文件操作使用 asyncio.Lock 保护
- Memory 数据目录在 `.gitignore` 中添加 `data/memory/`

---

## 设计哲学

### Memory 不只是存聊天记录

学习方案指出：Memory 不只是存聊天记录，而是明确什么需要跨步骤、跨任务保留。Phase 5 的三层记忆设计：
- **短期记忆**: 知道"这个用户之前研究了什么" → 避免重复劳动
- **工作记忆**: 知道"当前任务分解成了哪些步骤" → 有条理地执行
- **长期记忆**: 知道"之前的研究得出了什么结论" → 知识积累

### Planning 是先想再做

Phase 4 的 Agent 是"边做边想"（搜索 → 评估 → 可能再搜索）。Phase 5 增加"先想再做"（分解任务 → 按计划搜索 → 评估 → 可能修正计划）。Plan-and-Solve 比纯 ReAct 更适合复杂研究任务。

### Reflection 是自我质控

roadmap 和学习方案都强调：Agent 不能只"做完就交"，需要有自我检查和修正的能力。Phase 5 的 reflect 节点就是这个能力的工程化落地。

### Multi-Agent 不是越多越好

两份学习文档都明确警告：
> "多 Agent 适合讲故事和写简历，但生产中大多数场景单 Agent + 好的 Workflow 就够了"
> "不要为了多 Agent 而多 Agent"

Phase 5 实现 Multi-Agent 的目的是**学习 Supervisor 模式和角色分离设计**。通过单 Agent (agent_v2) 和 Multi-Agent 的并存，学习者可以对比：
- 单 Agent: 更快、更简单、调试更容易
- Multi-Agent: 角色职责更清晰、每个角色的 prompt 更专注、但延迟和成本更高

### 向后兼容

Phase 4 的 workflow 和 agent 模式完全不变。新增的 agent_v2 和 multi_agent 是新模式，通过 mode 参数选择。这保证了：
- Phase 4 的 135 个测试全部通过
- 现有的 API 调用不受影响
- 学习者可以对比 4 种模式的差异

---

## 完成标准

**Part A（Memory 系统）**:
- [ ] MemoryService 实现三层记忆（短期/工作/长期）
- [ ] 长期记忆持久化到 JSON 文件，重启后可恢复
- [ ] 短期记忆支持会话隔离（不同 session_id 互不影响）
- [ ] 记忆检索能找到相关洞见（关键词匹配）
- [ ] Memory 端点可查看/搜索/清除记忆
- [ ] MemoryService 测试全部通过

**Part B（Planning & Reflection）**:
- [ ] plan 节点能将研究主题分解为 2-4 个子问题
- [ ] reflect 节点能审查报告质量并给出 pass/revise 判定
- [ ] revise_report 节点能根据反馈修订报告
- [ ] recall_memory 节点能从 MemoryService 检索相关洞见
- [ ] save_memory 节点能将研究结果保存到 MemoryService
- [ ] agent_v2 图能正确执行完整流程: recall → plan → search → evaluate → report → reflect → save
- [ ] agent_v2 的 reflect → revise 循环最多执行 1 次
- [ ] agent_v2 测试全部通过

**Part C（Multi-Agent）**:
- [ ] 4 个角色节点（Researcher / Analyst / Writer / Reviewer）各自实现
- [ ] Multi-Agent 图能正确执行: plan → research → analyze → write → review → END
- [ ] analyst 的 evaluation 触发正确的条件路由
- [ ] reviewer 的 verdict 触发正确的条件路由
- [ ] 修订循环最多 1 次（防止死循环）
- [ ] max_iterations 正确限制搜索循环
- [ ] Multi-Agent 测试全部通过

**整体**:
- [ ] Phase 4 的 135 个测试仍全部通过
- [ ] 所有新测试通过
- [ ] `POST /api/v1/research` 支持 4 种 mode: workflow / agent / agent_v2 / multi_agent
- [ ] Memory 端点工作正常
- [ ] 不引入新的外部依赖（MemoryService 用标准库 json + asyncio）

---

## 关于代码复用

Phase 5 的很多逻辑可以复用 Phase 4 的已有代码：

| Phase 5 组件 | 可复用 Phase 4 的 |
|-------------|------------------|
| agent_v2 的 search 节点 | 直接复用 `make_search_node` |
| agent_v2 的 rewrite_query | 直接复用 `make_rewrite_query_node` |
| agent_v2 的 evaluate_results | 直接复用 `make_evaluate_results_node` |
| agent_v2 的 refine_query | 直接复用 `make_refine_query_node` |
| agent_v2 的 generate_report | 直接复用 `make_generate_report_node` |
| agent_v2 的 router | 复用 `_route_after_evaluation` 逻辑 |
| multi_agent 的 researcher | 复用 `make_search_node` 的逻辑 |
| multi_agent 的 refine_query | 复用 `make_refine_query_node` 的逻辑 |
| 辅助函数 | 直接复用 `_timestamp`, `_step`, `_format_evidence`, `_parse_web_search_results`, `_normalize_kb_result` 等 |

**原则**: 能 import 复用的就复用，不要复制粘贴。Multi-Agent 的 roles.py 可以直接导入 research/nodes.py 中的工厂函数和辅助函数。

---

## 不需要新增外部依赖

Phase 5 **不添加任何新依赖到 requirements.txt**。所有新功能使用已有依赖：
- LangGraph（已安装）— 图编排
- 标准库 json — 长期记忆持久化
- 标准库 asyncio — Lock 保护
- 标准库 pathlib — 文件路径操作
- httpx（已安装）— LLM 调用（通过 LLMService）

---

## 关于 LangGraph 版本兼容性

Phase 4 已安装 langgraph 0.6.11，Phase 5 继续使用相同版本。核心 API 不变：
- `StateGraph(state_schema)` 创建图
- `.add_node(name, function)` 添加节点
- `.add_edge(from, to)` 添加固定边
- `.add_conditional_edges(from, router_fn, mapping)` 添加条件边
- `.compile()` 编译图
- 编译后的图用 `.ainvoke(initial_state)` 异步执行

如果某个 API 在当前版本中有变化，以实际安装版本为准。

# Phase 4 Workflow & Agent 架构文档

## 1. 系统目标

Phase 4 在 Phase 0+1+2+3 的基础上完成两件事：

**Part A — 补齐工具层**：
- 新增 Web 搜索工具（Tavily REST API + httpx）
- 新增沙箱代码执行工具（asyncio.create_subprocess_exec）
- 工具注册表从 3 个工具扩展到 4-5 个

**Part B — 研究助理**：
- Workflow 模式：确定性 3 步工作流（rewrite → search → report）
- Agent 模式：LLM 动态决策循环（search → evaluate → refine/report）
- 两种模式共享 5 个节点函数，用 LangGraph StateGraph 编排
- 多源搜索：RAG + Web 并行，asyncio.gather

系统从"能调用工具的智能助手"升级为"能执行多步骤研究任务的智能体系统"。

## 2. Phase 4 架构概览

Phase 4 新增了以下层次：

- **Route 层**：新增 `research.py`，1 个端点
- **Schema 层**：新增 `research.py`，3 个数据模型
- **Service 层**：
  - 新增 `tools/web_search.py`、`tools/code_executor.py`（2 个新工具）
  - 新增 `research/` 模块（state + nodes + workflow + agent）
- **外部依赖**：新增 `langgraph>=0.2.0`

## 3. 模块划分（Phase 4 新增 / 修改）

### 3.1 `app/services/tools/web_search.py`（新增）

职责：
- 通过 Tavily REST API 搜索网络，返回格式化结果

核心类：
- `WebSearchTool`：封装 Tavily API 调用，实现 `__call__` 协议
- `build_web_search_tool(settings)` → `BuiltinTool`：工厂函数

调用流程：
```
handler({"query": "...", "max_results": 5})
  → 参数校验（空查询、范围检查）
  → httpx.AsyncClient.post("https://api.tavily.com/search")
  → 解析 response.json()["results"]
  → 格式化为编号列表（title + url + content[:300]）
```

设计要点：
- `WebSearchTool` 通过构造函数接收 `Settings`（获取 API key 和 base URL）
- 如果 `tavily_api_key` 为空，直接抛 `ValueError`（不发请求）
- API key 通过 `Authorization: Bearer` header 传递，不会出现在返回结果中
- 参数枚举校验：`search_depth` 只接受 `basic`/`advanced`，`topic` 只接受 `general`/`news`/`finance`

### 3.2 `app/services/tools/code_executor.py`（新增）

职责：
- 在独立子进程中执行 Python 代码，返回 stdout/stderr

核心函数：
- `_execute_python(arguments)` → `str`：异步执行函数
- `build_code_executor_tool()` → `BuiltinTool`：工厂函数（无需 settings）

执行流程：
```
handler({"code": "print(1+1)", "timeout": 10})
  → 长度检查（≤ 5000 字符）
  → 关键词黑名单检查（13 个模式）
  → tempfile.NamedTemporaryFile 写入代码
  → asyncio.create_subprocess_exec(sys.executable, temp_path)
  → asyncio.wait_for(process.communicate(), timeout)
  → 截断输出（stdout/stderr 各 ≤ 2000 字符）
  → finally: kill残留进程 + 删除临时文件
```

安全措施：

| 层次 | 措施 | 说明 |
|------|------|------|
| 输入限制 | 代码 ≤ 5000 字符 | 防止超大输入 |
| 关键词黑名单 | 13 个危险模式 | 拦截文件/网络/系统操作 |
| 进程隔离 | asyncio.create_subprocess_exec | 独立进程，崩溃不影响主服务 |
| 超时控制 | 1-30 秒硬限制 | 超时自动 kill |
| 输出限制 | stdout/stderr 各 ≤ 2000 字符 | 防止输出爆炸 |
| 清理 | finally 块删除临时文件 | 无残留 |

**注意**：关键词黑名单是教学级安全。生产环境应使用 Docker / nsjail 等真沙箱。

### 3.3 `app/services/research/state.py`（新增）

职责：
- 定义 LangGraph 状态 TypedDict

类型定义：

| 类型 | 说明 |
|------|------|
| `ResearchSearchResult` | 单条搜索结果：source, query, text_snippet, score, title, url |
| `ResearchStep` | 步骤记录：node, action, output_summary, timestamp |
| `ResearchState` | 完整状态：topic, queries, search_results, report, steps, iteration, max_iterations, evaluation, top_k |

累积语义字段（`Annotated[list, operator.add]`）：
- `queries`：每轮新增的查询追加到列表
- `search_results`：每轮搜索结果追加到列表
- `steps`：每个节点的 trace 追加到列表

覆盖语义字段：
- `report`、`iteration`、`evaluation`、`max_iterations`、`top_k`、`topic`

### 3.4 `app/services/research/nodes.py`（新增）

职责：
- 5 个节点工厂函数，产出符合 LangGraph 签名的 `async (state) -> dict` 处理器

节点清单：

| 工厂函数 | 节点名 | 依赖 | 输入 | 输出更新 |
|----------|--------|------|------|----------|
| `make_rewrite_query_node` | rewrite_query | LLMService | topic | queries, steps |
| `make_search_node` | search | RAGService, ToolRegistry | queries[-1] | search_results, steps, iteration |
| `make_evaluate_results_node` | evaluate_results | LLMService | search_results, topic | evaluation, steps |
| `make_refine_query_node` | refine_query | LLMService | queries, topic | queries, steps |
| `make_generate_report_node` | generate_report | LLMService | search_results, topic | report, steps |

**search 节点详细设计**：

```
make_search_node(rag_service, tool_registry)
  ↓
async def search(state):
    ┌─ search_knowledge_base()  ← RAGService.search()
    │     结果标记 source="knowledge_base"
    │
    ├─ search_web()             ← ToolRegistry.execute("web_search")
    │     如果 tavily_api_key 为空 → 跳过
    │     结果标记 source="web"
    │
    └─ asyncio.gather() 并行执行两者
    
    合并结果 → 返回 search_results + steps + iteration+1
```

错误处理策略：
- 每个节点 try/except 包裹核心逻辑
- 失败时：写入 steps 记录错误，返回 fallback 值（而非抛异常）
- search 节点：KB 和 Web 独立 try/except，互不影响

辅助函数：
- `_timestamp()`：UTC ISO 格式时间戳
- `_step(node, action, output_summary)`：构造 ResearchStep（output_summary 截断到 200 字符）
- `_format_evidence(state)`：格式化 search_results 为 LLM prompt 文本
- `_normalize_kb_result(item, query)`：RAG 结果转 ResearchSearchResult（支持 dict 和 object）
- `_parse_web_search_results(result, query)`：解析 web_search 格式化文本为 ResearchSearchResult 列表
- `_safe_load_json(value)`：安全 JSON 解析（失败返回 `{}`）

### 3.5 `app/services/research/workflow.py`（新增）

职责：
- 构建确定性工作流图

图结构：
```
START → rewrite_query → search → generate_report → END
```

- 3 个节点，全部用固定边连接
- 不使用 evaluate_results 和 refine_query
- `run_workflow()` 接收 topic、max_iterations、top_k 和三个服务对象
- 返回 `{report, steps, queries, iterations_used, search_result_count}`

### 3.6 `app/services/research/agent.py`（新增）

职责：
- 构建 LLM 驱动的 Agent 图

图结构：
```
START → rewrite_query → search → evaluate_results → [条件路由]
                                    ├─ "sufficient" → generate_report → END
                                    └─ "needs_more" → refine_query → search → evaluate_results → ...
```

- 5 个节点 + 1 个条件边
- `_route_after_evaluation(state)` 路由函数：
  - iteration ≥ max_iterations → `"sufficient"`（安全阀）
  - evaluation == "sufficient" → `"sufficient"`
  - 否则 → `"needs_more"`
- 双重安全检查：evaluate_results 节点也检查 max_iterations（belt and suspenders）

### 3.7 `app/schemas/research.py`（新增）

职责：
- 定义 Research API 的请求/响应模型

模型清单：

| 模型 | 字段 | 校验 |
|------|------|------|
| `StepRecord` | node, action, output_summary, timestamp | output_summary max_length=200 |
| `ResearchRequest` | topic, mode, max_iterations, top_k | topic min_length=2, mode Literal["workflow","agent"], max_iterations 1-10, top_k 1-20 |
| `ResearchResponse` | topic, mode, report, queries, steps, iterations_used, search_result_count | |

### 3.8 `app/api/routes/research.py`（新增）

职责：
- 暴露 `POST /api/v1/research` 端点

设计要点：
- 根据 `request.mode` 分发到 `run_workflow()` 或 `run_agent()`
- 模块级别创建 `llm_service`、`rag_service`、`tool_registry`（单例）
- 异常统一捕获，返回 500 + 通用错误信息（不泄露内部细节）

### 3.9 `app/core/config.py`（修改）

新增字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tavily_api_key` | str | `""` | Tavily Search API key |
| `tavily_base_url` | str | `https://api.tavily.com` | Tavily API 基础 URL |
| `enable_code_execution_tool` | bool | `False` | 是否注册 execute_python 工具 |
| `research_max_iterations` | int | 3 | Agent 默认最大搜索轮次 |
| `research_top_k` | int | 5 | 每次搜索的结果数 |

`tavily_api_key` 加入 `normalize_optional_text` field_validator。

### 3.10 `app/services/tool_registry.py`（修改）

修改点：
- `_register_defaults()` 新增 `web_search` 工具（始终注册）
- `_register_defaults()` 条件注册 `execute_python` 工具（仅当 `enable_code_execution_tool=True`）

### 3.11 `app/services/tools/__init__.py`（修改）

新增导出：`build_web_search_tool`、`build_code_executor_tool`

### 3.12 `app/main.py`（修改）

新增 `research_router` 注册。

## 4. 完整文件结构（Phase 4 视角）

```
8w-plan/
├── app/
│   ├── api/routes/
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── rag.py
│   │   ├── research.py              ← Phase 4 新增
│   │   └── tools.py
│   ├── core/
│   │   ├── config.py                ← Phase 4 修改（+5 字段）
│   │   └── logging.py
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── rag.py
│   │   ├── research.py              ← Phase 4 新增
│   │   └── tools.py
│   ├── services/
│   │   ├── research/                ← Phase 4 新增（整个目录）
│   │   │   ├── __init__.py
│   │   │   ├── state.py             ← ResearchState TypedDict
│   │   │   ├── nodes.py             ← 5 个节点工厂函数
│   │   │   ├── workflow.py          ← 确定性工作流图
│   │   │   └── agent.py             ← LLM Agent 图
│   │   ├── tools/
│   │   │   ├── __init__.py          ← Phase 4 修改（+2 导出）
│   │   │   ├── web_search.py        ← Phase 4 新增
│   │   │   ├── code_executor.py     ← Phase 4 新增
│   │   │   ├── get_current_time.py
│   │   │   ├── calculate.py
│   │   │   └── search_knowledge_base.py
│   │   ├── tool_registry.py         ← Phase 4 修改（+2 工具注册）
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   └── ...
│   └── main.py                      ← Phase 4 修改（+research router）
├── tests/
│   ├── test_tools_builtin.py        ← Phase 4 修改（+9 测试）
│   ├── test_tool_registry.py        ← Phase 4 修改（+1 测试）
│   ├── test_research_nodes.py       ← Phase 4 新增（9 测试）
│   ├── test_research_workflow.py    ← Phase 4 新增（1 测试）
│   ├── test_research_agent.py       ← Phase 4 新增（3 测试）
│   ├── test_research_endpoint.py    ← Phase 4 新增（5 测试）
│   └── ...
└── requirements.txt                 ← Phase 4 修改（+langgraph）
```

## 5. 数据流 / 调用链

### 5.1 Research API 调用链

```
POST /api/v1/research
  ↓
routes/research.py
  → 解析 ResearchRequest（topic, mode, max_iterations, top_k）
  → if mode == "workflow": run_workflow(...)
    elif mode == "agent": run_agent(...)
  → 返回 ResearchResponse
```

### 5.2 Workflow 执行流

```
run_workflow()
  → StateGraph(ResearchState)
  → add_node("rewrite_query", make_rewrite_query_node(llm_service))
  → add_node("search", make_search_node(rag_service, tool_registry))
  → add_node("generate_report", make_generate_report_node(llm_service))
  → add_edge(START → rewrite_query → search → generate_report → END)
  → graph.compile().ainvoke(initial_state)
  → 返回 {report, steps, queries, iterations_used, search_result_count}
```

### 5.3 Agent 执行流

```
run_agent()
  → StateGraph(ResearchState)
  → add 5 nodes
  → add_edge(START → rewrite_query → search → evaluate_results)
  → add_conditional_edges(evaluate_results → {sufficient: generate_report, needs_more: refine_query})
  → add_edge(refine_query → search)
  → add_edge(generate_report → END)
  → graph.compile().ainvoke(initial_state)
  → 返回 {report, steps, queries, iterations_used, search_result_count}
```

### 5.4 Search 节点内部数据流

```
search(state)
  ├── asyncio.gather:
  │     ├── search_knowledge_base()
  │     │     → RAGService.search(query, top_k)
  │     │     → 结果转 ResearchSearchResult (source="knowledge_base")
  │     │
  │     └── search_web()
  │           → 检查 tavily_api_key 是否配置
  │           → ToolRegistry.execute("web_search", {query, max_results})
  │           → 解析返回文本为 ResearchSearchResult (source="web")
  │
  └── 合并 kb_results + web_results
      → 返回 {search_results, steps, iteration+1}
```

## 6. 服务依赖关系

```
                    ┌─────────────────┐
                    │  research route  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
        ┌──────────┐  ┌──────────┐  ┌──────────────┐
        │LLMService│  │RAGService│  │ToolRegistry  │
        └──────────┘  └──────────┘  └──────┬───────┘
                                           │
                              ┌─────────────┼─────────────┐
                              ↓             ↓             ↓
                        ┌──────────┐ ┌───────────┐ ┌──────────┐
                        │web_search│ │code_exec  │ │3 old tools│
                        └────┬─────┘ └─────┬─────┘ └──────────┘
                             ↓             ↓
                        Tavily API   subprocess
```

research 模块**不直接依赖**任何外部 API。它通过 LLMService（LLM 调用）、RAGService（知识库搜索）、ToolRegistry（Web 搜索）间接访问外部资源。

## 7. 配置依赖关系

```
Settings
  ├── tavily_api_key ──→ web_search tool（空字符串时跳过 Web 搜索）
  ├── tavily_base_url ──→ web_search tool（API 端点）
  ├── enable_code_execution_tool ──→ ToolRegistry（是否注册 execute_python）
  ├── research_max_iterations ──→ 请求默认值（可被 API 参数覆盖）
  ├── research_top_k ──→ 请求默认值（可被 API 参数覆盖）
  ├── tool_call_timeout ──→ httpx 超时 + ToolRegistry.execute 超时
  └── 已有配置 ──→ LLM / Embedding / Qdrant / Rerank
```

## 8. 安全架构

### 8.1 Web Search 安全

| 风险 | 防护措施 |
|------|----------|
| API key 泄露 | key 只在 Authorization header 中，不出现在返回结果 |
| 空查询 | 参数校验，拒绝空字符串 |
| 参数越界 | max_results 限制 1-10，search_depth/topic 枚举校验 |
| API 失败 | 捕获 httpx 异常和非 200 状态码，抛出 ValueError |

### 8.2 代码执行安全

| 层次 | 防护 | 绕过难度 |
|------|------|----------|
| 输入长度 | ≤ 5000 字符 | 不可绕过 |
| 关键词黑名单 | 13 个模式 | 可绕过（编码/间接导入） |
| 进程隔离 | subprocess | 崩溃不影响主服务 |
| 超时控制 | ≤ 30 秒 | 不可绕过 |
| 输出限制 | stdout/stderr ≤ 2000 字符 | 不可绕过 |
| 默认关闭 | `enable_code_execution_tool=False` | 需要显式开启 |

**重要**：黑名单是教学级安全。生产环境必须升级到 Docker 容器或 gVisor 等真正的沙箱。

### 8.3 Research 安全

| 风险 | 防护措施 |
|------|----------|
| Agent 无限循环 | max_iterations 硬限制（1-10） |
| LLM 输出异常 | 每个节点 try/except，失败不崩溃 |
| 大量搜索结果 | top_k 限制（1-20） |
| 内部错误泄露 | 500 响应只返回通用错误信息 |

## 9. 与前序 Phase 的架构关系

### Phase 1 → Phase 4
- LLMService 被所有 5 个节点使用（查询重写、评估、优化、报告生成）
- 不修改 LLMService，完全复用 chat() 方法

### Phase 2 → Phase 4
- RAGService.search() 被 search 节点使用
- 不修改 RAGService，完全复用

### Phase 3 → Phase 4
- ToolRegistry 被 search 节点使用（执行 web_search）
- ToolRegistry 扩展了 _register_defaults()（新增 2 个工具）
- LLMService.chat_with_tools() 可使用新工具（web_search, execute_python）

**设计原则**：Phase 4 是 Phase 1-3 的**编排层**，不修改底层服务的核心逻辑。

## 10. 测试架构

### 10.1 测试分层

```
┌─────────────────────────────────────────────┐
│  test_research_endpoint.py (5 tests)        │  ← API 集成测试
│    mock run_workflow/run_agent               │
├─────────────────────────────────────────────┤
│  test_research_workflow.py (1 test)         │  ← 图集成测试
│  test_research_agent.py (3 tests)           │
│    mock LLMService + FakeRAGService         │
├─────────────────────────────────────────────┤
│  test_research_nodes.py (9 tests)           │  ← 节点单元测试
│    mock LLMService + RAGService + Registry  │
├─────────────────────────────────────────────┤
│  test_tools_builtin.py (+9 tests)           │  ← 工具单元测试
│  test_tool_registry.py (+1 test)            │
│    mock httpx / 真实 subprocess             │
└─────────────────────────────────────────────┘
```

### 10.2 测试策略

| 层次 | mock 什么 | 测试什么 |
|------|-----------|----------|
| 工具单元测试 | httpx.AsyncClient（web_search），无mock（code_executor） | 工具逻辑、参数校验、安全检查 |
| 节点单元测试 | LLMService.chat()、RAGService.search()、ToolRegistry.execute() | 状态更新、错误降级、多源合并 |
| 图集成测试 | LLMService.chat()、FakeRAGService、FakeToolRegistry | 端到端路径、条件路由、迭代控制 |
| API 集成测试 | run_workflow/run_agent（整个函数） | HTTP 状态码、响应格式、参数校验 |

### 10.3 关键测试场景

**新工具测试（9 条）**：
- web_search: 成功/空结果/API 错误/空查询
- code_executor: 成功/超时/关键词拦截/代码过长/stderr 输出

**节点测试（9 条）**：
- rewrite_query: 查询追加
- search: 多源合并 / RAG 失败降级 / Web 失败降级 / 无 Tavily key 跳过 / object 结果归一化
- evaluate_results: 正常评估 / 达到上限强制
- refine_query: 新查询追加
- generate_report: 报告生成

**Agent 测试（3 条）**：
- 第一轮即 sufficient → 直接生成报告
- 第一轮 needs_more → refine → 第二轮 sufficient → 生成报告
- 达到 max_iterations → 强制 sufficient → 生成报告

### 10.4 测试总量

| Phase | 测试数 | 累计 |
|-------|--------|------|
| Phase 0+1 | 2 | 2 |
| Phase 2 | 78 | 80 |
| Phase 3 | 23 | 103 |
| **Phase 4** | **32** | **135** |

# Phase 7（评估 / 安全 / 可观测性）— Codex GPT-5.5 长任务 Prompt

> 学习方案对照：Phase 7（Evaluation / Safety / Observability）
> 大项目里程碑：里程碑 7（评估报告 + 安全方案 + 监控仪表盘）
> 前置：Phase 6 已完成（207 tests passing）

---

## 任务总览

为现有 Agent 平台增加企业级 Agent 工程的"硬性要求"——评估、安全、可观测性。这是学习方案明确指出的**原课程盲区**，也是 Agent 工程师面试的高频考点。

### 学习目标
- 建立三层评估体系（组件级 / 系统级 / 用户级）
- 掌握 RAG 评估（Faithfulness / Context Precision / Answer Relevance）
- 掌握 Agent 评估（任务完成率 / 步骤效率 / 成本）
- 实现 Prompt Injection 基础防护和 Guardrails
- 建立轻量级 Tracing/Cost 系统（不依赖外部 SaaS）

### 不做什么
- 不集成 LangSmith / Langfuse 云服务（避免外部依赖；用本地 SQLite tracing 替代，理念可迁移）
- 不引入 RAGAS 包（手写实现核心指标，理解原理；可在 Capstone 阶段提及如何切换到 RAGAS）
- 不实现完整的 NeMo Guardrails（只做白名单 + 规则过滤）

---

## 项目当前状态

```
8w-plan/
├── app/
│   ├── services/
│   │   ├── evaluation_service.py       # 已有：仅 retrieval hit rate
│   │   ├── llm_service.py              # LLM 调用入口（要在这里埋点）
│   │   ├── tool_registry.py            # 工具调用入口（要在这里埋点）
│   │   ├── mcp/                        # Phase 6 新增
│   │   ├── memory_service.py
│   │   ├── research/                   # workflow / agent / agent_v2
│   │   └── multi_agent/
│   └── api/routes/
│       └── ...（已有 7 个 router: health/chat/rag/tools/research/memory/mcp）
├── eval/
│   └── sample_questions.jsonl          # 已有少量评估样本
├── scripts/
│   └── run_rag_eval.py                 # 已有简易 RAG 评估
└── tests/                              # 207 passing
```

---

## Phase 6 预检与修补（Codex 必须先做）

> 背景：Phase 6 MCP 主线已经跑通（207 tests passed，自连接 MCP smoke test 通过），但在进入 Phase 7 前需要先补几个 review 发现的工程化问题。先修这些点，再开始 Evaluation / Safety / Observability。

### P0.1 MCP Server 错误语义修复

当前问题：`app/services/mcp/server.py` 的 `call_tool` 把工具失败编码成普通文本 `ERROR: ...`，但没有设置 MCP 协议层的 `isError=True`。外部 MCP Client 会把失败当成成功文本，Agent 也无法可靠判断工具失败。

要求：
- 修改 `build_mcp_server()` 中的 `call_tool` handler。
- 当 `ToolCallRecord.error` 存在，或者 `ToolRegistry.execute()` 抛异常时，返回 `mcp.types.CallToolResult(content=[TextContent(...)], isError=True)`。
- 成功时仍返回正常 `TextContent` 或 `CallToolResult(isError=False)`。
- 更新 `tests/test_mcp_server.py`：错误 case 必须断言 `response.root.isError is True`。

示意：

```python
# app/services/mcp/server.py
# from mcp.types import CallToolResult, TextContent, Tool
#
# @server.call_tool()
# async def call_tool(name: str, arguments: dict) -> CallToolResult:
#     try:
#         record = await tool_registry.execute(name, arguments)
#         if record.error:
#             return CallToolResult(
#                 content=[TextContent(type="text", text=record.error)],
#                 isError=True,
#             )
#         return CallToolResult(
#             content=[TextContent(type="text", text=record.result)],
#             isError=False,
#         )
#     except Exception as exc:
#         return CallToolResult(
#             content=[TextContent(type="text", text=str(exc))],
#             isError=True,
#         )
```

### P0.2 外部 MCP 工具调用增加超时保护

当前问题：本地工具调用已经通过 `asyncio.wait_for(..., timeout=settings.tool_call_timeout)` 做了超时保护，但 `mcp__...` 外部工具路径没有超时。外部 MCP Server 卡住时，会拖死整个 ToolRegistry 调用。

要求：
- 修改 `ToolRegistry._execute_mcp_tool()`。
- 用 `asyncio.wait_for(self._mcp_runtime.execute_tool(...), timeout=self.settings.tool_call_timeout)` 包裹外部 MCP 调用。
- `TimeoutError` 时返回 `ToolCallRecord(error="MCP tool execution timed out.")`，不要抛给上层。
- 新增或扩展 `tests/test_tool_registry_with_mcp.py`，覆盖外部 MCP 工具超时。

### P0.3 Windows MCP 外部命令解析修复

当前问题：`Settings.parse_external_mcp_servers()` 使用默认 `shlex.split(command_line)`。在 Windows 单反斜杠路径中，例如 `C:\tools\node\npx.cmd ... C:\tmp`，默认 POSIX 语义会把反斜杠当转义，解析成错误路径。

要求：
- 修改 `app/core/config.py`。
- 推荐实现：`shlex.split(command_line, posix=(os.name != "nt"))`，并引入 `import os`。
- 新增 `tests/test_mcp_config.py` case：
	- `demo:C:\tools\node\npx.cmd -y server C:\tmp`
	- `demo:"C:\Program Files\nodejs\npx.cmd" -y server C:\tmp`
- 断言 command 和 args 保留正确 Windows 路径。

### P0.4 MCP Debug Invoke 的安全边界

当前问题：`POST /api/v1/mcp/tools/{tool_name}/invoke` 是一个直接执行外部 MCP 工具的 debug endpoint。只在本地开发时问题不大，但一旦部署到非 localhost 环境，它会成为高风险工具代理入口。

要求：
- Phase 7 的 Guardrails 集成时必须覆盖 MCP 工具调用。
- `GuardrailsService.validate_tool_call()` 需要识别 `mcp__<server>__<tool>` 工具名，并支持 MCP 工具白名单。
- `/api/v1/mcp/tools/{tool_name}/invoke` 在 guardrails enabled 时必须调用 `validate_tool_call()`。
- 若本阶段不做鉴权，必须在代码注释和 README/文档里明确：该 endpoint 是 local/debug-only，不应公网暴露。Phase 8 再用 API Key 中间件保护。

### P0.5 依赖版本固定

当前环境已验证通过：
- FastAPI `0.136.1`
- MCP `1.27.0`
- Pydantic `2.13.3`
- Uvicorn `0.46.0`

要求：
- 将 `requirements.txt` 中 `mcp>=1.2.0` 固定为 `mcp==1.27.0`，避免 fresh install 时漂到未验证版本。
- 保持已验证的 FastAPI / Pydantic / Uvicorn 版本组合。
- 新增一条文档说明：这次升级是为了兼容 MCP SDK 当前版本依赖的 Starlette 栈。

### P0.6 Cohere Rerank 重新验证与失败降级

背景：Phase 6 验证时真实 RAG ingest 成功，但 Cohere rerank 曾返回 `403 Forbidden`。现在外部 key/网络权限应已恢复，Codex 需要重新走一遍 Cohere 流程确认。

要求：
- 先运行一个最小 Cohere rerank 请求，确认 `https://api.cohere.com/v2/rerank` 返回 200。
- 再跑一次真实 RAG search / ask smoke：
	- 入库一个短文本或 PDF
	- `/api/v1/rag/search` 能返回 reranked results
	- `/api/v1/rag/ask` 能返回 answer + sources
- 如果仍然返回 403/429/5xx，不要把它归因到 MCP 或 Phase 7；记录为外部服务问题。
- 推荐补一个工程增强：`RerankService.rerank()` 在 403/429/5xx 时可以选择 fail-soft，记录 warning，并回退为 `candidates[:final_k]`。但如果当前测试依赖 hard failure，需先新增显式配置 `rerank_fail_soft: bool = True`，默认开启；单元测试覆盖开启/关闭两种行为。

### P0.7 预检测试要求

完成 P0 修补后先跑：

```powershell
conda activate ai-agent
python -m pytest -q tests/test_mcp_config.py tests/test_mcp_server.py tests/test_tool_registry_with_mcp.py tests/test_rerank_service.py
python -m pytest -q
```

预期：全量测试仍为 **207 passed 或更多**，然后才进入下面的 Phase 7 正式实现。

---

## Part A: 评估体系（Evaluation）

### A.1 设计

三层评估：

| 层级 | 关注点 | 实现 |
|------|--------|------|
| 组件级 | RAG 检索质量、单工具准确率 | `evaluation_service.py` 已有，扩展 |
| 系统级 | RAG 端到端、Agent 任务完成 | 新增 `agent_evaluator.py` |
| 数据集 | 标注样本、评估脚本 | `eval/` 扩展数据集 |

### A.2 扩展 evaluation_service — `app/services/evaluation_service.py`

新增 RAG 三大指标（LLM-as-judge 实现，不引入 RAGAS）：

```python
# async def llm_judge_faithfulness(
#     question: str,
#     answer: str,
#     contexts: list[str],
#     judge_fn: JudgeFn,           # 复用现有 JudgeFn 类型
# ) -> dict:
#     """
#     Faithfulness（忠实度）: answer 中的事实是否都能从 contexts 找到支持
#     - 把 answer 切分为原子断言（用 LLM 提取）
#     - 对每个断言用 LLM 判断 contexts 是否支持
#     - 返回 {"score": 0.0~1.0, "supported": int, "total": int, "claims": [...]}
#     """
#
# async def llm_judge_context_precision(
#     question: str,
#     contexts: list[str],
#     judge_fn: JudgeFn,
# ) -> dict:
#     """
#     Context Precision: 检索到的 contexts 中有多少与问题真正相关
#     - 对每个 context 用 LLM 判断 relevant/not_relevant
#     - 返回 {"score": 0.0~1.0, "relevant": int, "total": int}
#     """
#
# async def llm_judge_answer_relevance(
#     question: str,
#     answer: str,
#     judge_fn: JudgeFn,
# ) -> dict:
#     """
#     Answer Relevance: answer 是否切题（不答非所问）
#     - 让 LLM 给 1-5 分并解释
#     - 返回 {"score": 0.0~1.0, "raw_score": int, "reasoning": str}
#     """
#
# 关键: 所有 judge prompt 必须要求严格 JSON 输出，
# 解析失败时降级为 score=0.0 + reasoning="parse_failed"，不抛异常
```

### A.3 新增 Agent 评估 — `app/services/agent_evaluator.py`（新增）

```python
# 评估 Agent 端到端能力
#
# class AgentEvalCase(TypedDict):
#     topic: str
#     expected_keywords: list[str]      # 报告应包含的关键词
#     max_iterations: int
#     mode: str                          # "agent" | "agent_v2" | "multi_agent"
#
# async def evaluate_agent_run(
#     case: AgentEvalCase,
#     run_fn: Callable[..., Awaitable[dict]],
#     **run_kwargs,
# ) -> dict:
#     """
#     运行一次 Agent，返回:
#     - report: 生成的报告
#     - iterations_used: 实际迭代次数
#     - search_count: 搜索次数
#     - keyword_coverage: 关键词覆盖率 (0~1)
#     - latency_seconds: 端到端延迟
#     - completed: 是否成功完成
#     - error: 错误信息（若失败）
#     """
#
# async def evaluate_agent_batch(
#     cases: list[AgentEvalCase],
#     run_fn,
#     **run_kwargs,
# ) -> dict:
#     """
#     批量评估，返回汇总:
#     - total: 案例数
#     - completed_count
#     - success_rate (keyword_coverage >= 0.5)
#     - avg_iterations
#     - avg_latency
#     - per_case: list[dict]
#     """
```

### A.4 数据集扩展 — `eval/`

新增：
- `eval/rag_questions.jsonl` — 10+ 条 RAG 评估样本（question / expected_substring / reference_answer）
- `eval/agent_topics.jsonl` — 5+ 条 Agent 主题（topic / expected_keywords / mode）

数据集格式约定写在 `eval/README.md`。

### A.5 评估脚本

新增 `scripts/run_agent_eval.py`：
```python
"""
批量评估 Agent: 读取 eval/agent_topics.jsonl，对每个 topic 跑指定 mode，
输出 evaluation_report.json + 控制台表格。
"""
# 用法: python -m scripts.run_agent_eval --mode agent_v2 --limit 5
# 输出位置: eval/results/agent_eval_<timestamp>.json
```

修改 `scripts/run_rag_eval.py`：
- 新增 `--with-llm-judge` 选项，启用 faithfulness / context precision / answer relevance
- 输出位置: `eval/results/rag_eval_<timestamp>.json`

### A.6 评估端点（可选）— `app/api/routes/eval.py`（新增）

```python
# POST /api/v1/eval/rag
#   请求: {"limit": 10, "with_llm_judge": false}
#   响应: 评估指标汇总
#
# POST /api/v1/eval/agent
#   请求: {"mode": "agent_v2", "limit": 5}
#   响应: Agent 评估指标
#
# GET /api/v1/eval/results
#   返回 eval/results/ 下的历史评估结果列表
```

---

## Part B: Safety / Guardrails

### B.1 设计

三道防线：

1. **输入层**: 检测 Prompt Injection / 危险关键词
2. **工具层**: 工具白名单 + 参数验证
3. **输出层**: 敏感信息脱敏 / 输出长度限制

### B.2 新增 Guardrails 服务 — `app/services/guardrails_service.py`（新增）

```python
# class GuardrailsService:
#     def __init__(self, settings: Settings):
#         self.settings = settings
#         self._injection_patterns = [
#             "ignore previous instructions",
#             "ignore the above",
#             "disregard the above",
#             "you are now",
#             "pretend to be",
#             "system prompt",
#             "reveal your prompt",
#             "忽略之前的指令",
#             "忘记之前的设定",
#             "请扮演",
#         ]
#         self._sensitive_patterns = [
#             # 简单的 PII 模式（手机号、邮箱、身份证号 - 18位）
#             (re.compile(r"\b\d{11}\b"), "[PHONE]"),
#             (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
#             (re.compile(r"\b\d{17}[\dXx]\b"), "[ID_NUMBER]"),
#         ]
#
#     def check_input(self, user_input: str) -> dict:
#         """
#         返回:
#         {
#           "safe": bool,
#           "risk_level": "low" | "medium" | "high",
#           "matches": [{"pattern": "...", "type": "injection"}],
#           "sanitized_input": str  # 高风险时为提示文本，低风险时为原始输入
#         }
#         """
#
#     def sanitize_output(self, text: str) -> dict:
#         """
#         返回:
#         {
#           "sanitized": str,           # 脱敏后的文本
#           "redactions": [{"type": "phone", "count": int}, ...]
#         }
#         """
#
#     def validate_tool_call(self, tool_name: str, arguments: dict) -> dict:
#         """
#         检查工具白名单 + 参数中是否含命令注入字符
#         返回 {"safe": bool, "reason": str}
#         """
```

### B.3 集成到现有路径

**最小侵入原则**：通过依赖注入和可选参数，不修改既有测试。

修改：
- `app/services/llm_service.py`：`chat()` 增加 `guardrails: GuardrailsService | None = None` 参数。当传入时，对 user_message 做 `check_input`，对返回 reply 做 `sanitize_output`。默认 None 时行为完全不变。
- `app/services/tool_registry.py`：`execute()` 增加 `guardrails: GuardrailsService | None = None` 可选参数。当传入时，调用前做 `validate_tool_call`，失败则返回 ToolCallRecord(error=...)，不真正执行。
- `app/api/routes/chat.py` / `tools.py` / `research.py`：使用 `Depends()` 注入 GuardrailsService（默认启用）。新增 Settings 字段 `guardrails_enabled: bool = True`。

### B.4 配置 — Settings 扩展

```python
guardrails_enabled: bool = True
guardrails_strict_mode: bool = False  # True 时 medium 风险也拦截
```

---

## Part C: Observability（Tracing + Cost）

### C.1 设计

不依赖外部 SaaS，用 SQLite + 中间件实现轻量级 tracing：
- 每次 `LLMService.chat()` 调用记录: model / prompt_tokens / completion_tokens / latency / cost / parent_trace_id
- 每次 `ToolRegistry.execute()` 调用记录: tool_name / arguments_hash / latency / success / parent_trace_id
- 每次 Agent run 创建一个 root trace，子调用通过 `contextvars` 关联

### C.2 新增 TracingService — `app/services/tracing_service.py`（新增）

```python
# 使用 sqlite3 (标准库) + asyncio.Lock 保护写入
#
# class TraceRecord(TypedDict):
#     trace_id: str
#     parent_id: str | None
#     name: str                     # "llm_chat" | "tool_execute" | "agent_run" | ...
#     started_at: str               # ISO timestamp
#     ended_at: str
#     latency_ms: float
#     status: str                   # "ok" | "error"
#     metadata: dict                # 任意 JSON 可序列化
#     # for LLM:
#     model: str | None
#     prompt_tokens: int | None
#     completion_tokens: int | None
#     cost_usd: float | None
#
# class TracingService:
#     def __init__(self, settings: Settings):
#         self.db_path = Path(settings.tracing_db_path)
#         self._lock = asyncio.Lock()
#         self._init_db()  # CREATE TABLE IF NOT EXISTS traces (...)
#
#     @asynccontextmanager
#     async def trace(self, name: str, metadata: dict | None = None):
#         """
#         用法:
#             async with tracing.trace("llm_chat", {"model": "gpt-5.4"}) as ctx:
#                 ctx.set("prompt_tokens", 100)
#                 ctx.set("completion_tokens", 50)
#                 # ...
#         自动管理 trace_id（UUID） + parent_id（contextvar）+ 时间统计
#         异常时 status="error" 并记录 error message
#         """
#
#     async def query_traces(self, limit: int = 100, name: str | None = None) -> list[TraceRecord]: ...
#     async def get_cost_summary(self, since: str | None = None) -> dict:
#         """
#         返回:
#         {
#           "total_cost_usd": float,
#           "total_calls": int,
#           "total_tokens": {"prompt": int, "completion": int},
#           "by_model": {model_name: {calls, cost, tokens}, ...},
#           "since": str
#         }
#         """
```

### C.3 Cost 计算

新增 `app/services/cost_calculator.py`：

```python
# MODEL_PRICING (USD per 1M tokens):
# 配置化（从 Settings 或常量），方便后续修改
#
# DEFAULT_PRICING = {
#     "gpt-5.4": {"input": 5.0, "output": 15.0},          # 占位价格，实际部署需校准
#     "gpt-4o-mini": {"input": 0.15, "output": 0.60},
#     "text-embedding-3-large": {"input": 0.13, "output": 0.0},
# }
#
# def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
#     pricing = DEFAULT_PRICING.get(model, {"input": 0, "output": 0})
#     return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000
```

### C.4 集成到 LLMService 和 ToolRegistry

最小侵入扩展：

```python
# LLMService.chat() 增加可选参数 tracing: TracingService | None = None
# 当传入时，包裹在 async with tracing.trace("llm_chat", {"model": ...}):
# 解析 OpenAI 响应中的 usage 字段填入 tokens
# 调用 cost_calculator 计算 cost_usd
#
# ToolRegistry.execute() 同理，增加可选 tracing 参数
#
# 默认 None 时行为完全不变（保护现有测试）
```

### C.5 Tracing 端点 — `app/api/routes/observability.py`（新增）

```python
# GET /api/v1/observability/traces?limit=50&name=llm_chat
#   返回最近的 traces
#
# GET /api/v1/observability/cost?since=2026-05-01
#   返回成本汇总
#
# GET /api/v1/observability/agent_runs?limit=20
#   返回最近的 agent run trace 树（含子 trace 关联）
```

### C.6 Settings 扩展

```python
tracing_enabled: bool = True
tracing_db_path: str = "data/traces.db"
```

---

## Part D: 测试要求

### D.1 Evaluation 测试

**`tests/test_evaluation_llm_judge.py`**（新增）
- `test_faithfulness_full_support`: mock judge 返回所有 claims supported
- `test_faithfulness_partial`: 部分支持
- `test_faithfulness_parse_failure`: judge 返回非 JSON 时降级
- `test_context_precision_basic`
- `test_answer_relevance_high_score`
- `test_answer_relevance_low_score`

**`tests/test_agent_evaluator.py`**（新增）
- `test_evaluate_agent_run_keyword_coverage`: mock run_fn 返回带关键词的 report
- `test_evaluate_agent_run_failure`: run_fn 抛异常时优雅记录
- `test_evaluate_batch_aggregates_metrics`

**`tests/test_eval_endpoint.py`**（新增）
- `test_post_rag_eval_endpoint`
- `test_post_agent_eval_endpoint`
- `test_get_results_endpoint`

### D.2 Guardrails 测试

**`tests/test_guardrails_service.py`**（新增）
- `test_check_input_safe`: 普通输入通过
- `test_check_input_injection_detected`: "ignore previous instructions" 被识别
- `test_check_input_chinese_injection`: "忽略之前的指令"
- `test_sanitize_output_redacts_phone`
- `test_sanitize_output_redacts_email`
- `test_validate_tool_call_command_injection`
- `test_validate_tool_call_safe`

**`tests/test_guardrails_integration.py`**（新增）
- `test_chat_endpoint_blocks_injection`: 启用 guardrails 时 /chat 拦截
- `test_chat_endpoint_passes_clean_input`
- `test_chat_endpoint_without_guardrails_unchanged`: settings.guardrails_enabled=False 时行为不变

### D.3 Observability 测试

**`tests/test_tracing_service.py`**（新增，使用 `tmp_path` 提供 db）
- `test_trace_records_basic`: 一个 trace 进出后能查到
- `test_trace_with_parent`: 嵌套 trace 关联正确
- `test_trace_records_error`: 异常被记录为 status=error
- `test_query_traces_filters_by_name`
- `test_cost_summary_aggregates`

**`tests/test_cost_calculator.py`**（新增）
- `test_calculate_cost_known_model`
- `test_calculate_cost_unknown_model_returns_zero`

**`tests/test_observability_endpoint.py`**（新增）
- `test_get_traces_endpoint`
- `test_get_cost_endpoint`
- `test_get_agent_runs_endpoint`

### D.4 Smoke 测试 (manual)

`scripts/smoke_test_eval.py`：
```python
# 跑一次完整流程: 启动 app → 调用 /research → 调用 /eval/agent → 调用 /observability/cost
# 验证整个评估+追踪+成本链路打通
```

---

## 实现顺序

0. **Phase 6 预检修补**：完成 P0.1-P0.5（MCP error semantics / timeout / Windows parser / debug endpoint guardrails plan / dependency pin）并跑 MCP focused tests
1. **Cohere 重新验证**：按 P0.6 重新跑最小 rerank 请求 + 真实 RAG search/ask smoke；若仍失败，记录为外部服务问题并实现 fail-soft 方案
2. Settings 扩展（guardrails_enabled / tracing_enabled / tracing_db_path；如采用 rerank fail-soft，则加 rerank_fail_soft）
3. `evaluation_service.py` 扩展三个 LLM judge 函数 → 测试
4. `agent_evaluator.py` 新增 → 测试
5. `eval/rag_questions.jsonl` + `eval/agent_topics.jsonl` 数据集
6. `scripts/run_agent_eval.py` + 修改 `run_rag_eval.py`
7. `app/api/routes/eval.py` → 测试
8. `guardrails_service.py` → 测试（必须覆盖 `mcp__<server>__<tool>` 工具名）
9. `LLMService` / `ToolRegistry` / MCP debug invoke endpoint 接受可选 guardrails 参数 → 集成测试
10. `cost_calculator.py` → 测试
11. `tracing_service.py` → 测试
12. `LLMService` / `ToolRegistry` 接受可选 tracing 参数 → 测试
13. `app/api/routes/observability.py` → 测试
14. `app/main.py` 注册 eval_router + observability_router
15. 全量 `python -m pytest -q` —— 应有 **207 + Phase 7 新测试 = ~240+ tests**

---

## 完成标准

- [ ] 所有 Phase 6 旧测试通过（当前基线：207 passed）
- [ ] MCP Server 工具失败能返回协议层 `isError=True`
- [ ] 外部 MCP 工具调用受 `tool_call_timeout` 保护，超时返回 ToolCallRecord error
- [ ] Windows 风格 `MCP_EXTERNAL_SERVERS` 路径解析正确
- [ ] `requirements.txt` 固定已验证的 `mcp==1.27.0`
- [ ] 重新走 Cohere rerank 最小请求；若恢复，真实 RAG search/ask smoke 通过；若未恢复，记录外部 403/429/5xx 并启用/测试 fail-soft 策略
- [ ] `scripts/run_rag_eval.py --with-llm-judge` 能生成包含三大指标的报告
- [ ] `scripts/run_agent_eval.py` 能输出 success_rate / avg_iterations / avg_latency
- [ ] `/eval/rag` 和 `/eval/agent` 端点工作
- [ ] Guardrails 能拦截至少 5 种 injection 模式
- [ ] PII 脱敏对手机号/邮箱有效
- [ ] Guardrails 覆盖 MCP 工具白名单，`/api/v1/mcp/tools/{tool_name}/invoke` 不再是无保护的公网风险入口
- [ ] Tracing 写入 SQLite，能查询和汇总
- [ ] `/observability/cost` 返回模型分组成本
- [ ] LLMService / ToolRegistry 在不传 guardrails/tracing 时行为完全不变
- [ ] 不引入 LangSmith / Langfuse / RAGAS / NeMo Guardrails 等外部依赖

---

## Commit Message 模板

```
feat(phase7): evaluation, guardrails, and observability

Preflight hardening:
- Fix MCP server error propagation with isError=True
- Add timeout protection for external MCP tool calls
- Fix Windows MCP external server command parsing
- Pin verified MCP dependency version
- Re-run Cohere rerank and RAG smoke flow; add fail-soft path if needed

Evaluation:
- Add LLM-as-judge for Faithfulness / Context Precision / Answer Relevance
- Add agent-level evaluator with keyword coverage and latency metrics
- Add /api/v1/eval/* endpoints + scripts/run_agent_eval.py

Safety:
- Add GuardrailsService: prompt injection detection, PII redaction, tool whitelisting
- Integrate optional guardrails into LLMService, ToolRegistry, and MCP debug invoke endpoint (backward compatible)

Observability:
- Add lightweight TracingService backed by SQLite
- Add CostCalculator with per-model pricing table
- Add /api/v1/observability/traces|cost|agent_runs endpoints

Tests: 207 → ~240+ (all passing)
Refs: docs/Agent开发完整学习方案.md Phase 7 / Milestone 7
```

---

## 设计哲学

**为什么不用 RAGAS / LangSmith？**

教学目标是理解评估和追踪的"为什么"和"怎么做"。手写 LLM-as-judge 让你看到 prompt 模板的设计、JSON 解析的容错、指标聚合的逻辑。手写 SQLite tracing 让你理解 parent-child trace 关系、token usage 的提取、成本计算的位置。生产中可以无缝切到 RAGAS / LangSmith，因为协议都一样：trace tree + 指标聚合。

**为什么 Guardrails 用规则而非 LLM？**

第一道防线必须便宜、确定、快速。规则匹配不需要额外 LLM 调用，无延迟，可解释。LLM-based guardrails（如 NeMo Guardrails）适合作为第二道深度防线，本 phase 不实施。

**为什么所有集成点都是"可选参数 + 默认 None"？**

保护既有测试。这种设计模式叫 **"Outside-in optional dependency injection"**：现有调用点不改一行代码，新调用点显式传入服务。等积累了足够多的使用场景再考虑改造为 Depends() 必选注入。

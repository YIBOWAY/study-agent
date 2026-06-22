# Phase 7 架构文档：评估 / 安全 / 可观测性

---

## 1. 全局架构

```
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI 请求入口                             │
│                                                              │
│   每个请求经过：                                              │
│   ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│   │  Auth      │→ │ Guardrails │→ │ Business handler   │    │
│   │ (X-API-Key)│  │ (input chk)│  │ (chat/RAG/agent)   │    │
│   └────────────┘  └────────────┘  └─────┬──────────────┘    │
│                                          │                   │
│                          ┌───────────────┼───────────────┐   │
│                          ▼               ▼               ▼   │
│                   Guardrails       TracingService   Memory   │
│                   (output redact)  (span hierarchy)  (insight│
│                                                       store) │
│                                                              │
│   响应时附带：                                                │
│   - trace_id（写到 response header X-Trace-Id）              │
│   - sanitized output                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │ 异步落库
                     ▼
              ┌──────────────────────┐
              │ data/traces.db       │  ── 供 /observability 查询
              └──────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  评估流（离线/手动触发）                       │
│                                                              │
│  eval/rag_questions.jsonl  ─→  scripts/run_rag_eval.py      │
│  eval/agent_topics.jsonl   ─→  scripts/run_agent_eval.py    │
│                                       │                      │
│                                       ▼                      │
│                          evaluation_service.py               │
│                          agent_evaluator.py                  │
│                                       │                      │
│                                       ▼                      │
│                          eval/results/<timestamp>.json       │
│                          POST /api/v1/eval/{rag,agent}       │
│                          GET  /api/v1/eval/last              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 模块清单

| 文件 | 行数 | 职责 |
|------|------|------|
| `app/services/evaluation_service.py` | 231 | RAG 三大指标 LLM-as-judge + 老的 correctness/groundedness |
| `app/services/agent_evaluator.py` | 91 | Agent 任务级评估（关键词 + 延迟 + 迭代） |
| `app/services/guardrails_service.py` | 107 | 输入注入/输出 PII/工具调用 三层守卫 |
| `app/services/tracing_service.py` | 227 | SQLite 链路追踪 + ContextVar 父子串联 |
| `app/services/cost_calculator.py` | 13 | 模型价格表 + cost 估算 |
| `app/core/auth.py` | ~30 | API Key 验证（可选启用） |
| `app/api/dependencies.py` | ~40 | 统一注入 guardrails / tracing / auth |
| `app/api/routes/eval.py` | ~80 | /eval/* 端点 |
| `app/api/routes/observability.py` | ~70 | /observability/* 端点 |
| `scripts/run_rag_eval.py` | 修改 | 加 `--with-llm-judge` 模式 |
| `scripts/run_agent_eval.py` | 新增 | 跑 agent_topics.jsonl 批量评估 |

---

## 3. 关键数据结构

### 3.1 `traces` 表 schema

```sql
CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    parent_id TEXT,
    name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    status TEXT NOT NULL,
    metadata TEXT NOT NULL,    -- JSON
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd REAL
);
```

### 3.2 评估输出 JSON 结构

```json
{
  "started_at": "2026-05-02T08:30:00Z",
  "mode": "rag_with_judge",
  "summary": {
    "faithfulness": 0.85,
    "context_precision": 0.72,
    "answer_relevance": 0.91,
    "n_cases": 20
  },
  "per_case": [
    {"question": "...", "answer": "...", "faithfulness": 1, "context_precision": 0.6, "answer_relevance": 1, "judge_reason": "..."},
    ...
  ]
}
```

---

## 4. Tracing 的 ContextVar 设计细节

```python
_CURRENT_TRACE_ID: ContextVar[str | None] = ContextVar("current_trace_id", default=None)

@asynccontextmanager
async def trace(self, name, metadata=None):
    parent_id = _CURRENT_TRACE_ID.get()      # 拿当前栈顶
    trace_id = uuid4()
    token = _CURRENT_TRACE_ID.set(trace_id)  # 压栈
    try:
        yield ctx
    finally:
        _CURRENT_TRACE_ID.reset(token)       # 弹栈，恢复 parent
        await self._insert_record({...})
```

为什么必须用 ContextVar 而不是普通变量？
- FastAPI 是异步并发，多个请求同时跑
- 普通模块级变量会被并发请求互相覆盖
- `ContextVar` 在 asyncio Task 间隔离（每个 Task 一份），同一 Task 内嵌套时共享父子关系

> **小心**：在 `asyncio.create_task()` 创建的子任务里，ContextVar 会**继承调用时的快照**。如果你想让子任务追加自己的 trace，需要重新进入 `tracing.trace()` 上下文。

---

## 5. Guardrails 注入位置

```
chat / RAG / research / mcp.invoke 端点
        │
        ▼
get_guardrails_service() (FastAPI Depends)
        │
        ▼
GuardrailsService.check_input(user_text)
   ├── safe=True   → 进入业务
   └── safe=False  → 直接 403/400 + 日志

业务执行后：
        │
        ▼
GuardrailsService.sanitize_output(text)
   └── 替换 PII，附在 response 中

工具循环里：
        │
        ▼
GuardrailsService.validate_tool_call(name, args)
   └── 不安全直接拒绝执行
```

---

## 6. 评估服务的 fail-safe 设计

`evaluation_service.py` 里所有 LLM-as-judge 函数都遵循同一模板：

```python
async def llm_judge_faithfulness(question, answer, contexts, llm) -> dict:
    try:
        raw = await llm.chat(messages=[...], response_format={"type": "json_object"})
        parsed = json.loads(raw["content"])
        score = float(parsed.get("score", 0))
        reason = str(parsed.get("reason", ""))
    except (json.JSONDecodeError, ValueError, KeyError):
        return {"score": 0.0, "reason": "judge parse failed"}
    if not 0 <= score <= 1:
        return {"score": 0.0, "reason": "score out of range"}
    return {"score": score, "reason": reason}
```

要点：
- JSON 解析失败 → 默认 0 分（保守）
- 分数越界 → 视为无效
- 永不向上抛异常（避免一个评委失败拉崩整批）

---

## 7. 配置项

```python
# Guardrails
guardrails_enabled: bool = True
guardrails_strict_mode: bool = False
guardrails_allowed_tools: str = "*"
guardrails_allowed_mcp_tools: str = "*"

# Tracing
tracing_enabled: bool = True
tracing_db_path: str = "data/traces.db"
max_trace_age_days: int = 30   # 预留：定期清理

# Auth
api_key_required: bool = False
api_key: str = ""

# Cost
default_model_input_price_per_1m: float = 5.0
default_model_output_price_per_1m: float = 15.0
```

---

## 8. 测试矩阵

| 文件 | 覆盖点 |
|------|--------|
| test_guardrails_service.py | 三层守卫的 happy/sad path（含中文注入） |
| test_guardrails_integration.py | guardrails 串到 chat/research/mcp 端点 |
| test_evaluation_llm_judge.py | 三大 LLM-as-judge 指标 + 解析失败容错 |
| test_agent_evaluator.py | 单 case + 批量统计 |
| test_eval_endpoint.py | /eval/* 三个端点 |
| test_eval_scripts.py | scripts/run_rag_eval, scripts/run_agent_eval CLI 入口 |
| test_tracing_service.py | trace 嵌套；并发不串号；落库字段齐全 |
| test_cost_calculator.py | 已知/未知模型；输入输出分开计价 |
| test_observability_endpoint.py | trace 列表/详情/cost-summary |
| test_auth.py | API key required on/off；header 缺失 |
| test_chat_stream.py / test_chat_stream_endpoint.py | 流式输出 + guardrails 兼容 |
| test_research_stream*.py | SSE + tracing 串联 |

合计 ~80 测试。

---

## 9. 已知限制与改进路径

| 限制 | 当前 | 改进方案 |
|------|------|---------|
| 价格表是占位 | 写死在代码里 | 改用 settings + 启动时从远程拉 |
| Email regex 偏宽 | `[\w.+-]+@[\w-]+\.[\w.-]+` | 严格 TLD 校验 |
| 流式 PII 漏检 | 单 chunk 正则 | 加 200 字符滑动 buffer |
| trace 无清理任务 | 表会无限增长 | 加 cron 删除超过 max_trace_age_days 的记录 |
| LLM judge 单评委 | 依赖单个模型 | 上 panel-of-judges（3 个评委多数表决） |

# Phase 7：评估、安全与可观测性

> 目标：把 Agent 从"能 demo"升级到"敢上生产"——给系统装上**评估指标、安全护栏、链路追踪、成本核算**
> 前置要求：Phase 5（多 Agent）+ Phase 6（MCP）
> 预计时间：3-5 天

---

## 0. 为什么这一阶段是面试杀手锏

面试官问到这几个问题，没准备好的人立刻露怯：
1. "你怎么知道你的 RAG 答得好不好？"
2. "用户要是发个 prompt injection 把你 system prompt 偷走怎么办？"
3. "上线后哪个 trace 慢了你怎么定位？"
4. "Agent 一个月烧多少 token？怎么管的？"

Phase 7 的答案就是：
- **Evaluation**：RAGAS-style 三大指标 + Agent 任务级评估 + LLM-as-judge
- **Guardrails**：输入注入检测、输出 PII 脱敏、工具白名单、参数过滤
- **Tracing**：SQLite 落盘的链路 + 父子关系 + contextvar 自动串联
- **Cost**：按模型表算 input/output token 单价

---

## 1. 评估体系：三层视角

```
第 1 层：组件级（可重复）
  ├── RAG 评估（retrieval + generation 分别打分）
  └── 工具调用准确率

第 2 层：系统级（端到端）
  ├── Agent 任务完成率
  ├── 平均迭代次数 / 平均延迟
  └── Token / 成本

第 3 层：用户级（生产中后期补）
  ├── 满意度 / 留存
  └── Bug report
```

### 1.1 RAG 三大指标（`evaluation_service.py`）

| 指标 | 含义 | 实现 |
|------|------|------|
| **Faithfulness** | 答案是否被 context 支持（无幻觉） | LLM-as-judge：把 answer + context 给评委 LLM，输出 0/1 + 理由 |
| **Context Precision** | 检索 top-k 里有多少是真用上的 | LLM 判断每个 chunk 与 question 的相关性 |
| **Answer Relevance** | 答案是否切题（不是答非所问） | LLM 让评委从答案反向生成问题，与原问题做语义相似 |

> **学习要点**：LLM-as-judge 最大的坑是**评委本身可能错**。本项目策略：
> - 用比生成更强的模型当评委（生成 gpt-5.4，评委也用 gpt-5.4，但 temperature=0）
> - 强制 JSON 输出，解析失败默认打"未通过"（fail-safe）
> - 留接口让你换更强的评委

### 1.2 Agent 评估（`agent_evaluator.py`）

```python
class AgentEvalCase(TypedDict):
    topic: str
    expected_keywords: list[str]   # 报告里应出现的关键词
    max_iterations: int
    mode: str                       # workflow/agent/agent_v2/multi_agent
```

指标：
- `keyword_coverage`：关键词命中率（穷人版 recall）
- `iterations_used`：实际迭代次数
- `latency_seconds`：端到端延迟
- `success_rate`：批量统计中 keyword_coverage ≥ 0.5 的比例

> **为什么不直接用 LLM 评 Agent 报告？** 可以做，但成本高。本项目分两层：先用关键词覆盖快速过滤，对疑似失败的再让 LLM-as-judge 复核。

### 1.3 评估端点

```
POST /api/v1/eval/rag      # 跑 eval/rag_questions.jsonl
POST /api/v1/eval/agent    # 跑 eval/agent_topics.jsonl
GET  /api/v1/eval/last     # 拿最近一次结果
```

---

## 2. 安全：Guardrails 三道防线

### 2.1 输入侧：Prompt Injection 检测

`check_input(user_input)` 用模式匹配（中英文）：

| 风险等级 | 模式举例 | 处理 |
|---------|---------|------|
| **High** | "ignore previous instructions" / "忽略之前的指令" | 直接阻断，返回固定提示 |
| **Medium** | "you are now" / "请扮演" | strict 模式下阻断，否则放行+打标 |
| **Low** | （未命中） | 直接放行 |

> **常见误区**：以为 guardrails 能挡住所有注入。**它挡不住**。这只是最便宜的第一道筛，配合 system prompt 设计 + 输出审查才有用。

### 2.2 输出侧：PII 脱敏

`sanitize_output(text)` 正则替换：
- 11 位连续数字 → `[PHONE]`
- email → `[EMAIL]`
- 18 位身份证 → `[ID_NUMBER]`

> **已知局限**：流式场景下 PII 可能跨 chunk，正则匹配不到。本项目接受这个 trade-off（速度 > 100% 脱敏），生产中可加 buffer 缓冲。

### 2.3 工具侧：白名单 + 参数过滤

```python
validate_tool_call(tool_name, arguments):
    if not _is_tool_allowed(tool_name): block
    if any dangerous pattern in flatten(arguments): block
```

危险参数模式：`;`, `&&`, `||`, `` ` ``, `$(`, `powershell`, `cmd.exe`。

工具白名单分两部分：
- `GUARDRAILS_ALLOWED_TOOLS` — 控制本地工具
- `GUARDRAILS_ALLOWED_MCP_TOOLS` — 控制 MCP 工具（默认 `*`，强烈建议生产收紧）

---

## 3. 可观测性：TracingService

### 3.1 数据模型（SQLite 表 `traces`）

```
trace_id PK | parent_id FK | name | started_at | ended_at | latency_ms |
status | metadata(JSON) | model | prompt_tokens | completion_tokens | cost_usd
```

### 3.2 用 contextvar 自动串联父子关系

```python
async with tracing.trace("rag.ask") as ctx:        # 顶层
    async with tracing.trace("retrieve") as r:     # 自动认 rag.ask 为 parent
        ...
    async with tracing.trace("llm.chat") as l:     # 同样
        l.set("model", "gpt-5.4")
        l.set("prompt_tokens", 123)
```

`_CURRENT_TRACE_ID: ContextVar` 在 `trace()` 进入时设新值、退出时还原——完美兼容并发请求互不干扰。

### 3.3 查询端点

```
GET /api/v1/observability/traces           # 列出最近 N 条
GET /api/v1/observability/traces/{id}      # 单条详情（含子节点）
GET /api/v1/observability/cost-summary     # 按模型/按天聚合成本
```

### 3.4 与 LangSmith / Langfuse 的对比

我们手写的 SQLite tracing 是**教学版**：能看清原理。生产建议：
- 流量小：保留 SQLite
- 流量中：换 Langfuse 自部署（开源）
- 流量大：上 LangSmith（付费）或 OpenTelemetry → Tempo/Jaeger

接入只需把 `TracingService.start_trace` 替换为对应 SDK 调用。

---

## 4. Cost 核算（`cost_calculator.py`）

```python
PRICES = {  # USD per 1M tokens
    "gpt-5.4": {"input": 5.0, "output": 15.0},
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    ...
}

def estimate_cost(model, prompt_tokens, completion_tokens) -> float:
    p = PRICES.get(model, DEFAULT)
    return (prompt_tokens / 1e6) * p["input"] + (completion_tokens / 1e6) * p["output"]
```

> **建议**：把价格表挪到配置或拉取上游 API。当前是占位价。

每次 LLM 调用都把 `cost_usd` 写进 trace，便于事后审计。

---

## 5. 关键设计决策

| 决策点 | 我们的选择 | 为什么 |
|--------|----------|------|
| Tracing 后端 | 自写 SQLite | 教学清楚，零依赖 |
| 评估范式 | 关键词 + LLM-as-judge 双层 | 平衡成本与精度 |
| Guardrails 默认开关 | 开 | 否则 prod 会忘记 |
| LLM judge 解析失败 | 默认判失败 | fail-safe |
| 注入鉴权方式 | API Key（X-API-Key 头） | 简单够用，未来可换 OAuth |
| Cost 单位 | USD，存在 traces 表 | 便于聚合查询 |

---

## 6. 完成本阶段你应当能回答

- [ ] RAGAS 三个指标分别衡量什么？什么场景哪个更重要？
- [ ] LLM-as-judge 的常见失败模式有哪些？怎么缓解？
- [ ] Prompt injection 为什么靠 guardrails 挡不住？还需要哪些手段？
- [ ] 怎么把 trace 的 parent_id 串起来？为什么要用 ContextVar 而不是参数传递？
- [ ] Token 成本占大头通常是 input 还是 output？为什么？
- [ ] 流式输出下 PII 脱敏的难点是什么？

---

## 7. 推荐资料

| 主题 | 资源 |
|------|------|
| RAGAS 论文 | "RAGAs: Automated Evaluation of RAG" (2023) |
| LLM-as-judge | "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" |
| Prompt injection | OWASP LLM Top 10 / "Universal and Transferable Adversarial Attacks on Aligned Language Models" |
| Tracing 设计 | OpenTelemetry 规范的 trace_id/span_id 部分 |
| Guardrails | NeMo Guardrails 文档、Guardrails AI 文档 |

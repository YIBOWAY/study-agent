# Part 6: Framework Comparisons（LangChain 轨）

> 接 Part 5。你已经**真的**用过 LangChain idioms 搭 Parts 1–5。Part 6 不是再看宣传册，而是用**同一套 weights** 重新打分：handwritten / langchain / langgraph / crewai 记录谁赢——分数可逐项复算。

预计时间：50–75 分钟。

## Learner Contract

- **你会构建**：`ComparisonTask` + `FrameworkProfile` + 矩阵 + `recommend_profile`；跑离线 `run_lc_baseline`。
- **你会解释**：为什么不同 task weights 会选出不同赢家；`total_score` 公式；profile 是课程记录不是 SDK wrapper。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_comparisons.py -q`。
- **诚实边界**：不安装 CrewAI/LangGraph 也能评分；LG 高分项（state_resume）是**预期记录**，完整 LG 轨在 F4–F5。

## 与 handwritten 对照

| Handwritten | 本轨 |
| --- | --- |
| `course.framework_comparisons` | `langchain_course.comparisons` |
| `run_handwritten_task` + FakeModel | `run_lc_baseline` + 真实 LC tool loop |
| `FrameworkProfile` 记录 | 同语义，分数反映“学完 LC 后”的诚实更新 |
| 禁止第三方 framework import | 同样禁止；profile 不是 wrapper |

> [DD] **为何学完 LC 还要再比一次？** 主课 Part 6 在“没用过真框架”时训练判断力；本 Part 用真实 LC 体验校准：inspectability 依赖你是否坚持 `AgentStep` 纪律；team_cost 往往对 LC 更友好。

## Section 1：固定考试

七维 `SCORE_CRITERIA`：`inspectability, offline_testing, typed_contracts, state_resume, multi_agent, product_boundary, team_cost`。

```text
total = round( sum(score(c)*weight(c)) / sum(weights), 4 )
strengths: score >= 0.80
tradeoffs: score < 0.55
tie-break: (-total_score, profile_id)
```

```text
fixed task + fixed fixture + fixed metric
                 |
        run evidence + score profile
                 |
          recommendation record
```

## Section 2 [BUILD]：inspectability task

```bash
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_course.comparisons import (
    build_inspectability_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
    run_lc_baseline,
)

task = build_inspectability_task()
matrix = build_recommendation_matrix(task, default_framework_profiles())
winner = recommend_profile(matrix, task_id=task.id)
print(winner.profile_id, winner.total_score, winner.strengths)
assert winner.profile_id == "handwritten"

baseline = run_lc_baseline(task)
print(baseline.step_sequence, baseline.tool_call_count)
assert "tool_call" in baseline.step_sequence
assert "user_message" in baseline.step_sequence
assert "model_response" in baseline.step_sequence
```

## Section 3 [INSPECT]：确认 baseline 不是“画出来的轨迹”

`run_lc_baseline` 内部调用 Part 1 的 `run_tool_calling_agent`，使用真实
`BaseChatModel`、`AIMessage.tool_calls` 和 `BaseTool.invoke`，只是模型输出
确定且离线。

> [CHECK] deterministic 不等于 synthetic。确定性模型仍经过框架执行路径；
> 手工创建 `AgentStep(...)` 列表则绕过了被比较对象。

## Section 4 [BUILD]：换 weights

```python
resume = build_state_resume_task()
matrix2 = build_recommendation_matrix(resume, default_framework_profiles())
winner2 = recommend_profile(matrix2, task_id=resume.id)
assert winner2.profile_id == "langgraph"
```

> [CHECK] **同一批 profile，不同 task，不同赢家**——这才是选型记录，不是“永远手写”或“永远框架”。

## Section 5 [BREAK / FIX]：怎样做出一张骗人的评分表

- 只给 LangChain 跑真实任务，其他候选只凭印象打分；
- 中途换 fixture，却保留旧分数；
- 把“框架自带”和“课程自己补的 `AgentStep`”混成一个分数；
- 用手工轨迹冒充真实 baseline。

修复：在 recommendation 旁保存 task id、weights、运行证据和人工判断说明。

> [TRAP] 本课的 profile 仍是课程记录，不是自动 benchmark。`run_lc_baseline`
> 只让 LC 的执行证据变真实，不会自动证明所有主观分数正确。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_comparisons.py -q
```

## Section 6 [REFLECT]：写一条可反驳的结论

写三段：在你刚完成的 LC 体验里，inspectability / team_cost / state_resume 各怎么变？下一步为什么还要学 LangGraph 轨？

下一章 Part 7：diagnostics、JSONL、approval、sandbox。

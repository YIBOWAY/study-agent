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
| `run_handwritten_task` + FakeModel | `run_lc_baseline` + scripted `AgentStep` |
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

## Section 2 [BUILD]：inspectability task

```bash
uv run python
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
```

## Section 3 [BUILD]：换 weights

```python
resume = build_state_resume_task()
matrix2 = build_recommendation_matrix(resume, default_framework_profiles())
winner2 = recommend_profile(matrix2, task_id=resume.id)
assert winner2.profile_id == "langgraph"
```

> [CHECK] **同一批 profile，不同 task，不同赢家**——这才是选型记录，不是“永远手写”或“永远框架”。

## Section 4：Reflection

写三段：在你刚完成的 LC 体验里，inspectability / team_cost / state_resume 各怎么变？下一步为什么还要学 LangGraph 轨？

下一章 Part 7：diagnostics、JSONL、approval、sandbox。

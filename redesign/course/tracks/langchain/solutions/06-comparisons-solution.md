# Solution 06 — Comparisons（LangChain 轨）

## L1 winners

```python
from langchain_course.comparisons import (
    build_inspectability_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
)

profiles = default_framework_profiles()
w1 = recommend_profile(
    build_recommendation_matrix(build_inspectability_task(), profiles),
    task_id="task_inspectability",
)
w2 = recommend_profile(
    build_recommendation_matrix(build_state_resume_task(), profiles),
    task_id="task_state_resume",
)
assert w1.profile_id == "handwritten"
assert w2.profile_id == "langgraph"
```

## L2 手算

`total = (1.0*1 + 0.0*1) / 2 = 0.5`；`inspectability` 进 strengths，`team_cost` 进 tradeoffs。

## L3 笔记要点

- 离线 Capstone 证明的是**合同可检查**，不是“永远拒绝框架”。
- 迁产品 runtime 需要 adapter、测试、文档与 phase 计划——不能把 `langchain_course` 直接塞进 `apps/`。

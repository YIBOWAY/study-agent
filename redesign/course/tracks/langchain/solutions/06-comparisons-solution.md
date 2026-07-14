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

`run_lc_baseline` 还应出现 `user_message/model_response/tool_call/tool_result`。
这些步骤来自实际 `run_tool_calling_agent`，不是评分模块手工造出的轨迹。

## L2 手算

`total = (1.0*1 + 0.0*1) / 2 = 0.5`；`inspectability` 进 strengths，`team_cost` 进 tradeoffs。

若 weights 改为 3 和 1，结果是 `(1*3 + 0*1) / 4 = 0.75`。分母永远是
实际参与任务的权重总和，不是固定七维数量。

## L3 笔记要点

- 离线 Capstone 证明的是**合同可检查**，不是“永远拒绝框架”。
- 迁产品 runtime 需要 adapter、测试、文档与 phase 计划——不能把 `langchain_course` 直接塞进 `apps/`。

推荐模板：

- **Chosen:** 当前继续 handwritten 产品 runtime。
- **Rejected:** 直接让 teaching package 进入 apps。
- **Because:** LC baseline 降低组装成本，但产品边界和 state resume 仍需证据。
- **Evidence:** 固定 task 的真实 tool-loop trail + 可复算 matrix。
- **Revisit when:** F4/F5 完成 checkpoint/resume Capstone 后。

## 常见错误

把 deterministic 当成“不真实”，或把 synthetic 当成“离线测试”。判断标准是
是否经过被评估的框架执行路径，而不是是否访问网络。

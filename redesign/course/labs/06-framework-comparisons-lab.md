# Lab 06: Framework Comparisons

## Goal

这个 lab 会带你亲手做四件事：

1. 跑 Phase 6 的 focused comparison tests。
2. inspect 手写 `AgentRunner` 的 echo-tool trajectory。
3. 打印 recommendation matrix。
4. 改 task 权重，观察推荐结果为什么会变。

预计时间：45 到 60 分钟。

## Setup

所有命令默认从 `redesign/` 运行：

```bash
cd redesign
```

先跑 focused tests：

```bash
uv run pytest tests/course/test_framework_comparisons.py -q
```

你应该看到全部通过。

## Exercise 1: Inspect The Handwritten Baseline

打开 Python shell：

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

粘贴：

```python
from course.framework_comparisons import build_echo_tool_task, run_handwritten_task

task = build_echo_tool_task()
summary = run_handwritten_task(task)

print(task.expected_event_sequence)
print(summary.to_record())
```

自查：

```python
assert summary.event_sequence == task.expected_event_sequence
assert summary.tool_call_count == 1
assert summary.error_count == 0
```

## Exercise 2: Print The Recommendation Matrix

还在同一个 shell，粘贴：

```python
from course.framework_comparisons import (
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
)

tasks = [build_echo_tool_task(), build_state_resume_task()]
matrix = build_recommendation_matrix(
    tasks=tasks,
    profiles=default_framework_profiles(),
)

for item in matrix:
    print(item.to_record())

for task in tasks:
    print("winner", task.id, recommend_profile(matrix, task_id=task.id).profile_id)
```

自查：

```python
assert recommend_profile(matrix, task_id="echo_tool_trace").profile_id == "handwritten"
assert recommend_profile(matrix, task_id="state_resume_workflow").profile_id == "langgraph"
```

## Exercise 3: Change Task Weights

复制 `echo_tool_trace`，但把 `state_resume` 权重调高：

```python
from course.framework_comparisons import ComparisonTask

echo = build_echo_tool_task()
state_heavy_echo = ComparisonTask(
    id="state_heavy_echo",
    title="State-heavy echo",
    system_prompt=echo.system_prompt,
    user_message=echo.user_message,
    model_responses=echo.model_responses,
    tool_name=echo.tool_name,
    tool_description=echo.tool_description,
    tool_argument_name=echo.tool_argument_name,
    required_capabilities=echo.required_capabilities,
    expected_event_sequence=echo.expected_event_sequence,
    weights={
        "state_resume": 0.55,
        "multi_agent": 0.15,
        "inspectability": 0.10,
        "offline_testing": 0.05,
        "typed_contracts": 0.05,
        "product_boundary": 0.05,
        "team_cost": 0.05,
    },
)

new_matrix = build_recommendation_matrix(
    tasks=[state_heavy_echo],
    profiles=default_framework_profiles(),
)
print(recommend_profile(new_matrix, task_id="state_heavy_echo").to_record())
```

观察：同一个 echo fixture，因为权重变了，推荐会偏向 state/resume 更强的 profile。

## Exercise 4: Break The Criteria

故意写一个不存在的 criteria：

```python
ComparisonTask(
    id="bad",
    title="Bad task",
    system_prompt=echo.system_prompt,
    user_message=echo.user_message,
    model_responses=echo.model_responses,
    tool_name=echo.tool_name,
    tool_description=echo.tool_description,
    tool_argument_name=echo.tool_argument_name,
    required_capabilities=echo.required_capabilities,
    expected_event_sequence=echo.expected_event_sequence,
    weights={"marketing_claims": 1.0},
)
```

你应该看到：

```text
ValueError: unknown weight criteria: marketing_claims
```

## Reflection

做完以后，回答：

1. 为什么同一个 task 可以因为权重不同而推荐不同框架？
2. `run_handwritten_task()` 为什么必须真的跑 `AgentRunner`，而不是只返回假 summary？
3. `FrameworkProfile` 和真实 framework adapter 有什么区别？
4. 如果一个框架必须联网才能跑 echo-tool task，它会在哪个 criteria 上扣分？
5. 如果未来要把 LangGraph 做成真实 adapter，应该放进 `research_core` 还是单独的 comparison/adapters 区域？

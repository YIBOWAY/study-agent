# Solution 06: Framework Comparisons

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 Python snippets 默认从 `redesign/` 运行。

## Focused Test Check

```bash
uv run pytest tests/course/test_framework_comparisons.py -q
```

期望结果：

```text
6 passed
```

如果数量未来增加，以实际测试数为准；关键是 focused comparison tests 必须全部通过。

## Exercise 1 Solution

Shell:

```bash
PYTHONPATH=.:packages/research_core/src uv run python
```

Python:

```python
from course.framework_comparisons import build_echo_tool_task, run_handwritten_task

task = build_echo_tool_task()
summary = run_handwritten_task(task)

assert summary.event_sequence == task.expected_event_sequence
assert summary.tool_call_count == 1
assert summary.error_count == 0
assert summary.final_answer == "The echo tool returned hello."
```

What this proves:

- the handwritten baseline executes real `AgentRunner` behavior;
- the event sequence is inspectable;
- the comparison task is offline and deterministic.

## Exercise 2 Solution

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

assert recommend_profile(matrix, task_id="echo_tool_trace").profile_id == "handwritten"
assert recommend_profile(matrix, task_id="state_resume_workflow").profile_id == "langgraph"
```

What this proves:

- a recommendation is task-relative;
- the simple echo-tool task rewards inspectability and offline testing;
- a state/resume-heavy workflow rewards checkpoint and graph-state ergonomics.

## Exercise 3 Solution

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
winner = recommend_profile(new_matrix, task_id="state_heavy_echo")

assert winner.profile_id == "langgraph"
```

What this proves:

- changing weights changes the engineering question;
- the matrix is not trying to crown one permanent winner;
- framework choice should follow the task, not the other way around.

## Exercise 4 Solution

```python
try:
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
except ValueError as exc:
    assert "unknown weight criteria" in str(exc)
else:
    raise AssertionError("Expected invalid criteria to fail")
```

What this proves:

- comparison criteria are controlled by code;
- accidental or vague metrics are rejected;
- reports can stay aligned with executable checks.

## Final Takeaway

The important lesson is:

```text
Compare frameworks by pinning the task, fixture, and metric first.
```

For this redesign, handwritten runtime remains the teaching and product
baseline. Frameworks become useful when a task's requirements, such as
checkpoint/resume or graph orchestration, justify the extra dependency and team
cost.

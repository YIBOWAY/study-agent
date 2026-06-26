# Solution 04: Delegation Runtime

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 snippets 都从 `redesign/` 的 Python shell 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Imports And Child Runner

```python
from research_core.delegation import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationRuntime,
    DelegationTask,
)
from research_core.runtime import (
    AgentMessage,
    AgentRunResult,
    MessageRole,
    RunEvent,
    RunEventType,
    event_type_sequence,
)


class FixedChildRunner:
    def run(self, run_id: str, system_prompt: str, user_message: str) -> AgentRunResult:
        final = AgentMessage(
            id="child_final",
            role=MessageRole.ASSISTANT,
            content="Child reviewed delegated evidence.",
        )
        return AgentRunResult(
            final_message=final,
            messages=(final,),
            events=(
                RunEvent(
                    id="child_evt_1",
                    run_id=run_id,
                    type=RunEventType.MODEL_REQUEST,
                    payload={"prompt": user_message},
                ),
                RunEvent(
                    id="child_evt_2",
                    run_id=run_id,
                    type=RunEventType.MODEL_RESPONSE,
                    payload={"content": final.content},
                ),
            ),
        )
```

## Exercise 1 Solution

```python
role = AgentRolePolicy(
    id="role_reviewer",
    name="Reviewer",
    system_prompt="Review only the delegated evidence.",
    tool_names=["search"],
    skill_names=["summarize"],
    memory_kinds=["episodic"],
    max_steps=2,
)

task = DelegationTask(
    id="task_1",
    parent_run_id="parent_run",
    child_run_id="child_run_1",
    objective="Summarize the supplied evidence.",
    role=role,
    context_messages=[
        AgentMessage(
            id="msg_allowed",
            role=MessageRole.USER,
            content="Allowed evidence excerpt.",
        )
    ],
    metadata={"private_parent_history": "This must not leak."},
)

assert task.role.system_prompt == "Review only the delegated evidence."
assert task.context_messages[0].content == "Allowed evidence excerpt."
```

What this proves:

- The role owns the child system prompt and scope.
- The task owns the objective, run IDs, and allowed context messages.
- Parent-private metadata is stored on the task but is not automatically child context.

## Exercise 2 Solution

```python
runtime = DelegationRuntime(child_runner_factory=lambda role: FixedChildRunner())
result = runtime.run_task(
    task,
    budget=DelegationBudget(max_child_runs=1, max_steps_per_child=2, max_total_steps=2),
)

assert result.status.value == "completed"
assert result.final_message.content == "Child reviewed delegated evidence."
assert len(result.child_events) == 2
```

What this proves:

- `DelegationRuntime` can run a deterministic child runner.
- Child final message is preserved.
- Child events are preserved separately from parent events.

## Exercise 3 Solution

```python
assert event_type_sequence(result.parent_events) == [
    "delegate_start",
    "delegate_event",
    "delegate_event",
    "delegate_finish",
]
assert result.parent_events[1].payload["child_event"]["type"] == "model_request"
assert result.parent_events[2].payload["child_event"]["type"] == "model_response"
assert "private_parent_history" not in result.child_events[0].payload["prompt"]
```

What this proves:

- Parent timeline records the delegation lifecycle.
- Child events are embedded as records, not mixed into parent messages.
- Parent-private metadata does not leak into child prompt text.

## Exercise 4 Solution

```python
too_large_role = AgentRolePolicy(
    id="role_large",
    name="Large Role",
    system_prompt="Try to do too much.",
    max_steps=5,
)

too_large_task = DelegationTask(
    id="task_too_large",
    parent_run_id="parent_run",
    child_run_id="child_run_large",
    objective="Overrun the child budget.",
    role=too_large_role,
)

try:
    runtime.run_task(
        too_large_task,
        budget=DelegationBudget(max_child_runs=1, max_steps_per_child=2, max_total_steps=2),
    )
except ValueError as exc:
    error_message = str(exc)
else:
    raise AssertionError("Expected budget preflight to fail")

assert "max_steps 5 exceeds max_steps_per_child 2" in error_message
```

What this proves:

- Delegation budget is checked before child execution.
- A role that asks for too many steps is rejected deterministically.
- Budget errors are contract errors, not model-output surprises.

## Final Takeaway

The important lesson is:

```text
Delegation is a contract: role, context, budget, event trail, and merge status.
```

Multi-agent systems become debuggable only when child work stays isolated and visible.

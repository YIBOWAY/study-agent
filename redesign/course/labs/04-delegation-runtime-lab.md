# Lab 04: Delegation Runtime

## Goal

这个 lab 会带你亲手跑四种情况：

1. 创建一个 child role 和 delegation task。
2. 用固定 child runner 执行 delegation。
3. 检查 parent `delegate_*` event sequence。
4. 故意超过预算，观察 preflight failure。

预计时间：45 到 60 分钟。

## Setup

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开，后面的练习会复用变量。

先粘贴 imports 和固定 child runner：

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

## Exercise 1: Create Role And Task

粘贴：

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

print(task.role.name)
print(task.context_messages[0].id)
```

自查：

```python
assert task.role.system_prompt == "Review only the delegated evidence."
assert task.context_messages[0].content == "Allowed evidence excerpt."
```

## Exercise 2: Run The Delegated Task

粘贴：

```python
runtime = DelegationRuntime(child_runner_factory=lambda role: FixedChildRunner())
result = runtime.run_task(
    task,
    budget=DelegationBudget(max_child_runs=1, max_steps_per_child=2, max_total_steps=2),
)

print(result.status.value)
print(result.final_message.content)
```

你应该看到：

```text
completed
Child reviewed delegated evidence.
```

自查：

```python
assert result.status.value == "completed"
assert result.final_message.content == "Child reviewed delegated evidence."
```

## Exercise 3: Inspect Parent Delegation Events

粘贴：

```python
print(event_type_sequence(result.parent_events))
print(result.parent_events[1].payload["child_event"]["type"])
print("private_parent_history" in result.child_events[0].payload["prompt"])
```

你应该看到：

```text
['delegate_start', 'delegate_event', 'delegate_event', 'delegate_finish']
model_request
False
```

自查：

```python
assert event_type_sequence(result.parent_events) == [
    "delegate_start",
    "delegate_event",
    "delegate_event",
    "delegate_finish",
]
assert result.parent_events[1].payload["child_event"]["type"] == "model_request"
assert "private_parent_history" not in result.child_events[0].payload["prompt"]
```

## Exercise 4: Break The Budget

粘贴：

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
    print(str(exc))
else:
    raise AssertionError("Expected budget preflight to fail")
```

你应该看到类似：

```text
task task_too_large role max_steps 5 exceeds max_steps_per_child 2
```

## Reflection

做完以后，回答：

1. `AgentRolePolicy` 管什么，`DelegationTask` 管什么？
2. parent 为什么不能把全部 history 默认传给 child？
3. `delegate_event` 的 payload 为什么要保存 child event record？
4. 预算失败为什么应该在 child runner 调用前发生？
5. 如果 child 失败，parent 应该丢掉它还是把失败变成可检查的 result？

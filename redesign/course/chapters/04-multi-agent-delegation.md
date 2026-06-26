# Chapter 04: Multi-Agent Delegation

## Goal

这一章补上 Phase 4 的学习路径：一个父 Agent 怎样把一小块任务交给 child agent，同时不把父上下文、预算和失败处理搅成一团。

学完以后，你应该能看懂这条主线：

```text
AgentRolePolicy
  -> DelegationTask
  -> DelegationRuntime
  -> delegate_* RunEvent records
  -> DelegationResult
  -> DelegationMergeResult
```

预计时间：60 到 75 分钟。

## Before You Start

请先完成：

- `01-agent-kernel-foundations.md`
- `03-memory-and-skills.md`

这一章不会做真正的并发、远程 worker 或网络版 A2A。Phase 4 只建立确定性的本地 delegation contract。

## The Idea In Plain Language

Multi-agent 不等于“多叫几个模型一起聊”。

在这个项目里，delegation 至少要回答五个工程问题：

1. child agent 扮演什么角色？
2. child agent 能看到哪些 context？
3. child agent 最多能跑多少步？
4. child agent 的 events 怎么回到 parent timeline？
5. child 失败后，parent 怎么保留这个事实而不是假装没发生？

Phase 4 的答案是：用 `DelegationTask` 明确任务，用 `DelegationBudget` 控制成本，用 parent `delegate_*` events 保存轨迹，用 `DelegationMergeResult` 显示哪些 child result 还没有解决。

## Core Objects

| Object | Plain Meaning | Why It Exists |
| --- | --- | --- |
| `AgentRolePolicy` | child agent 的角色边界 | 保存 system prompt、允许的 tools/skills/memory kinds 和 max_steps |
| `DelegationTask` | parent 交给 child 的任务 | 保存 objective、child run id、允许的 context messages |
| `DelegationBudget` | 本地预算 | 控制 child 数量、每个 child 步数和总步数 |
| `DelegationRuntime` | delegation 执行器 | 调 child runner，并把 child events 包成 parent events |
| `DelegationResult` | 单个 child 的结果 | 保存 status、final message、child events、parent events 和 error |
| `DelegationMergeResult` | parent 合并记录 | 保留成功决策和 unresolved conflicts |
| `A2AAdapterStub` | 远程边界占位 | 只做 deterministic export，不做真实网络发送 |

## Minimal Example

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

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

runtime = DelegationRuntime(child_runner_factory=lambda role: FixedChildRunner())
result = runtime.run_task(
    task,
    budget=DelegationBudget(max_child_runs=1, max_steps_per_child=2, max_total_steps=2),
)

print(result.status.value)
print(event_type_sequence(result.parent_events))
print(result.final_message.content)
print("private_parent_history" in result.child_events[0].payload["prompt"])
```

你应该看到：

```text
completed
['delegate_start', 'delegate_event', 'delegate_event', 'delegate_finish']
Child reviewed delegated evidence.
False
```

这里最重要的不是 child 回了什么，而是 parent event sequence 里清楚记录了 delegation 的开始、child event、结束。

## Child Context Isolation

`DelegationTask` 允许 parent 显式传入 `context_messages`。它不会把 parent 全部历史自动塞给 child。

这条边界很重要：

- child 只应该看到完成任务需要的材料；
- parent 的内部分析、私有 metadata、其他 child 的输出不应该默认泄露；
- system prompt 由 `AgentRolePolicy` 管，不允许 context messages 自己带 system message。

所以 `metadata={"private_parent_history": ...}` 不会进入 `compile_child_prompt()` 的输出。

## Budget Accounting

Phase 4 的预算很朴素，但足够表达三个限制：

- `max_child_runs`: 最多派几个 child。
- `max_steps_per_child`: 单个 child 最多几次 model request。
- `max_total_steps`: 所有 child 加起来最多几次 model request。

这些限制先在本地 deterministic runtime 里测试清楚，后面做 async execution 或真实远程 worker 时才有可继承的 contract。

## Failure Lab Preview

故意让 role 的 `max_steps` 超过预算：

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
```

你应该看到类似：

```text
task task_too_large role max_steps 5 exceeds max_steps_per_child 2
```

这个错误发生在 child runner 被调用之前。预算不合格的任务不应该先跑起来再说。

## Merge And A2A Boundary

`DelegationMergeResult` 的默认规则很保守：只有 `completed` child result 被视为可接受决策，其他状态会进入 `unresolved_conflicts`。

`A2AAdapterStub` 也很保守：它能把 task 导出成 deterministic envelope，但 `send()` 会明确抛出 `NotImplementedError`。这避免课程或测试误以为远程 agent transport 已经完成。

## Product Integration

Phase 5 的 Workbench 会把 Phase 4 对象映射到这些 UI：

- delegation tree：显示 parent run 和 child run。
- run timeline：显示 `delegate_start`、`delegate_event`、`delegate_finish`。
- child trace drawer：查看 embedded child event records。
- budget panel：显示 child count 和 step limits。
- merge review panel：显示 unresolved conflicts。

如果没有 Phase 4 的 event 和 result contract，这些 UI 只能展示一堆不可复盘的“子任务摘要”。

## Eval Gate

项目级检查：

```bash
uv run pytest tests/research_core/test_delegation_runtime.py tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py -q
uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_runtime.py tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py
```

核心自查：

```python
assert event_type_sequence(result.parent_events) == [
    "delegate_start",
    "delegate_event",
    "delegate_event",
    "delegate_finish",
]
```

## Checkpoint

继续 Phase 5 前，用自己的话回答：

1. `AgentRolePolicy` 和 `DelegationTask` 为什么要分开？
2. 为什么 child context 不能默认继承 parent history？
3. `delegate_event` 为什么要嵌入 child event record？
4. 预算为什么要在 child runner 前先检查？
5. 为什么 `A2AAdapterStub.send()` 现在必须抛错？

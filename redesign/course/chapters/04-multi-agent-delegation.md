# Part 4: Multi-Agent Delegation - 把小任务交给下属但不失控

> 接 Part 3。你已经让本地论文研究助手有了 memory notebook 和 skill package。Part 4 继续训练同一个习惯：不要只问 "child 最后答了什么"，要问 "child 看到了什么、花了多少步、失败有没有留在 parent 的审计面上"。

预计时间：80 到 110 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要知道 Part 1 的 event trail，也知道 Part 3 的 memory/skill 边界为什么不能乱塞上下文。
- **Before you start**: 先完成 Part 1 的 Agent Kernel、Part 2 的 evidence chain、Part 3 的 Memory and Skills。
- **You will build**: 一个完全离线的 delegation loop：parent 生成任务单，child 只看允许的 context，runtime 记录 parent `delegate_*` events，预算按 child `MODEL_REQUEST` 计数，merge 结果保留未解决冲突。
- **You will be able to explain**: 为什么 role 和 task 要分开；为什么 delegated child 不能继承 parent 全部历史；为什么有些失败会抛 `ValueError`，有些失败会变成 `FAILED` result；为什么 merge 不能吞掉 failed child。
- **You will prove it works by running**: `PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_delegation_runtime.py tests/research_core/test_delegation_contracts.py tests/research_core/test_multi_agent_evals.py -q`。
- **Offline guarantee**: 所有 child runner 都是本地 deterministic stub；没有真实并发、网络 worker、远程 A2A transport、API key 或外部服务。

## 你的本地论文研究助手现在需要：会分工

研究员已经让助手维护证据链和记忆。现在任务变大了：

> "这批 RAG 评测论文里，请一个 reviewer 只检查 citation links，另一个 reviewer 只检查 evaluation risks，然后把结果合并。"

听起来像 "多叫两个 agent" 就行。但工程上马上有三个坑：

1. **下属看到了不该看的 parent context**：parent 的私有推理、未确认 memory、另一个 child 的草稿，都被塞进 child prompt。
2. **下属跑超预算**：child 多次请求模型，parent 只看到最后一句 "done"，不知道成本已经失控。
3. **失败被吞了**：一个 child 失败，parent 只把成功 child 的摘要拼成 final answer，看起来一切正常。

Part 4 解决的是这个问题：把一小块研究任务外包给专注的下属，但 context、预算、失败都必须可检查。

> [BIG] **大局观**：Part 3 教你不要让 memory/skill 污染 parent context；Part 4 把同一个边界扩展到 child agent。delegated child 必须只拿到任务所需材料，不能继承 unfiltered parent memory。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [x] Part 2: Research Core, evidence chain
  [x] Part 3: Memory and Skills
  [*] Part 4: Delegation
      [*] child context isolation
      [*] step budget accounting
      [*] parent delegation event trail
      [*] unresolved conflicts stay visible
  [ ] Part 5: Workbench UI
  [ ] Part 6: Framework comparison
  [ ] Part 7: Production readiness
```

## Section 1 [LIGHT Concept]: 外包给专注下属

Delegation 的心智模型很简单：你不是把整个大脑复制给下属，而是给他一张工牌、一张任务单、一笔预算，然后要求他交回可审计回执。

| System piece | Plain-language model | What to inspect |
| --- | --- | --- |
| `AgentRolePolicy` | 工牌：这个下属是谁，能用什么 | `system_prompt`, `tool_names`, `skill_names`, `memory_kinds`, `max_steps` |
| `DelegationTask` | 任务单：这次只让他做什么、看什么 | `objective`, `child_run_id`, `context_messages`, `metadata` |
| `DelegationBudget` | 预算：最多几个下属、每人几步、总共几步 | `max_child_runs`, `max_steps_per_child`, `max_total_steps` |
| `DelegationRuntime` | 派活的人：调用 child runner，并给 parent 留回执 | `run_task(...)`, `run_many(...)` |
| parent `delegate_*` events | 回执：开始、child 每个 event、结束 | `delegate_start`, `delegate_event`, `delegate_finish` |
| `DelegationResult` | 单个下属的结果单 | `status`, `final_message`, `child_events`, `step_count`, `error_message` |
| `DelegationMergeResult` | 汇总和未结清清单 | `decisions`, `unresolved_conflicts`, `summary` |

> [DD] **设计决策**：R4 不做真实并发，也不接远程 worker。先把本地 deterministic contract 教清楚：context 怎么编译、预算怎么数、失败怎么留下。否则后面做 async 或 A2A 只是把不清楚的边界放大。

> [TRAP] **诚实边界**：`tool_names` / `skill_names` / `memory_kinds` 写在工牌上，但 `DelegationRuntime` **不会**自动按这些列表过滤 child 的 `ToolRuntime`、Skill 或 Memory。当前真正 enforced 的是 `max_steps` 与 `DelegationBudget`。工厂侧应调用 `filter_tools_for_role(role, tool_names)`（或等价检查）再注册工具；`skill_names` / `memory_kinds` 仍是声明式标签，留给后续 phase 接入。


### Delegation flow

```text
Parent run
  |
  | creates DelegationTask(role, objective, context_messages)
  v
DelegationRuntime.run_task(task, budget)
  |
  | 1. validate role.max_steps against DelegationBudget
  | 2. emit parent DELEGATE_START
  | 3. child_runner.run(
  |        run_id=task.child_run_id,
  |        system_prompt=task.role.system_prompt,
  |        user_message=compile_child_prompt(task),
  |    )
  | 4. wrap every child RunEvent as parent DELEGATE_EVENT
  | 5. count child MODEL_REQUEST events as step_count
  | 6. emit parent DELEGATE_FINISH
  v
DelegationResult(status, final_message, child_events, parent_events, error_message)
```

### Budget accounting

```text
Preflight checks
  role.max_steps <= max_steps_per_child
  min(role.max_steps, max_steps_per_child) <= max_total_steps

Observed runtime checks
  step_count = count(child events where type == MODEL_REQUEST)
  if step_count > min(role.max_steps, max_steps_per_child):
      return DelegationResult(status=FAILED)

run_many sequential budget
  remaining = max_total_steps
  for each task:
      allowed_max_steps must fit in remaining
      run child
      observed step_count must fit in remaining
      remaining -= observed step_count
```

> [CHECK] **检查一下**：`step_count` 不是 child event 总数，而是 child `MODEL_REQUEST` 的数量。`MODEL_RESPONSE` 会进入审计轨迹，但不消耗这里的 step budget。

## Section 2 [FULL Build]: Run One Delegated Review

从 `redesign/` 打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

先准备 imports 和一个 deterministic child runner：

```python
from research_core.delegation import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationMergeResult,
    DelegationRuntime,
    DelegationTask,
)
from research_core.delegation.runtime import compile_child_prompt
from research_core.runtime import (
    AgentMessage,
    AgentRunResult,
    MessageRole,
    RunEvent,
    RunEventType,
    event_type_sequence,
)


class ScriptedChildRunner:
    def __init__(self, request_count=1):
        self.request_count = request_count

    def run(self, run_id: str, system_prompt: str, user_message: str) -> AgentRunResult:
        events = []
        for index in range(self.request_count):
            events.append(
                RunEvent(
                    id=f"{run_id}_request_{index + 1}",
                    run_id=run_id,
                    type=RunEventType.MODEL_REQUEST,
                    payload={"prompt": user_message, "index": index + 1},
                )
            )

        final = AgentMessage(
            id=f"{run_id}_final",
            role=MessageRole.ASSISTANT,
            content=f"{run_id} reviewed delegated evidence.",
        )
        events.append(
            RunEvent(
                id=f"{run_id}_response",
                run_id=run_id,
                type=RunEventType.MODEL_RESPONSE,
                payload={"content": final.content},
            )
        )
        return AgentRunResult(
            final_message=final,
            messages=(final,),
            events=tuple(events),
        )
```

### Build: role and task

```python
role = AgentRolePolicy(
    id="role_reviewer",
    name="Reviewer",
    system_prompt="Review only delegated evidence.",
    tool_names=("search",),
    skill_names=("summarize",),
    memory_kinds=("episodic",),
    max_steps=2,
)

task = DelegationTask(
    id="task_a",
    parent_run_id="parent_run",
    child_run_id="child_a",
    objective="Check whether the evidence supports claim A.",
    role=role,
    context_messages=(
        AgentMessage(
            id="ctx_1",
            role=MessageRole.USER,
            content="Evidence excerpt A",
        ),
    ),
    metadata={"private_parent_history": "must not leak"},
)
```

`AgentRolePolicy` 是工牌，`DelegationTask` 是任务单。注意 `metadata` 不是 child context；它是 parent 侧的附加记录。

### Inspect: compile the child prompt

```python
print(compile_child_prompt(task))
```

Expected output:

```text
Objective:
Check whether the evidence supports claim A.

Context Messages:
- ctx_1 (user): Evidence excerpt A
```

`compile_child_prompt(task)` 只包含 objective 和 `context_messages`。它没有 `metadata`，也没有 parent 的完整 memory。

> [TRAP] **常见误解**：`task.metadata` 存在，不等于 child 能看到。要判断 child 看到了什么，检查 `compile_child_prompt(task)` 或 child `MODEL_REQUEST` event payload，而不是猜。

### Run and inspect the parent trail

```python
runtime = DelegationRuntime(child_runner_factory=lambda role: ScriptedChildRunner())
result = runtime.run_task(
    task,
    budget=DelegationBudget(
        max_child_runs=1,
        max_steps_per_child=2,
        max_total_steps=2,
    ),
)

print(result.status.value)
print(result.step_count)
print(event_type_sequence(result.parent_events))
print(result.final_message.content)
print("private_parent_history" in result.child_events[0].payload["prompt"])
```

Expected output:

```text
completed
1
['delegate_start', 'delegate_event', 'delegate_event', 'delegate_finish']
child_a reviewed delegated evidence.
False
```

这几个输出分别证明：

- child 成功完成，`status` 是 `completed`。
- 只有一个 child `MODEL_REQUEST`，所以 `step_count` 是 `1`。
- parent timeline 有开始、两个 child event 回执、结束。
- child prompt 没有泄露 parent-private metadata。

```python
print(result.parent_events[-1].payload["status"])
print(result.parent_events[-1].payload["step_count"])
```

Expected output:

```text
completed
1
```

## Section 3 [FULL Build]: Run Many And Merge

单个 delegation 只能证明一个下属能跑。真正的 Multi-Agent 问题是：多个 child 加起来有没有超过总预算？失败有没有留在汇总里？

先建两个一人一步的任务：

```python
one_step_role = AgentRolePolicy(
    id="role_one_step",
    name="One Step Reviewer",
    system_prompt="Review exactly one delegated slice.",
    max_steps=1,
)


def make_review_task(task_id: str, child_run_id: str, objective: str) -> DelegationTask:
    return DelegationTask(
        id=task_id,
        parent_run_id="parent_batch",
        child_run_id=child_run_id,
        objective=objective,
        role=one_step_role,
    )


batch_tasks = (
    make_review_task("review_eval", "child_eval", "Check evaluation evidence."),
    make_review_task("review_citation", "child_citation", "Check citation evidence."),
)

batch_results = runtime.run_many(
    batch_tasks,
    budget=DelegationBudget(
        max_child_runs=2,
        max_steps_per_child=1,
        max_total_steps=2,
    ),
)

print([item.task.id for item in batch_results])
print([item.step_count for item in batch_results])
print(sum(item.step_count for item in batch_results))
```

Expected output:

```text
['review_eval', 'review_citation']
[1, 1]
2
```

`run_many` 是顺序预算核算：第一个 child 用掉 1 步，第二个 child 再用掉 1 步，总共刚好等于 `max_total_steps=2`。

现在把一个成功结果和一个失败结果合并：

```python
overflow_runtime = DelegationRuntime(
    child_runner_factory=lambda role: ScriptedChildRunner(request_count=5)
)
overflow_result = overflow_runtime.run_task(
    task,
    budget=DelegationBudget(
        max_child_runs=1,
        max_steps_per_child=2,
        max_total_steps=2,
    ),
)

merge = DelegationMergeResult.from_results(
    [result, overflow_result],
    summary="One child passed; one child needs review.",
)

print(merge.summary)
print([item.status.value for item in merge.decisions])
print([(item.task.id, item.status.value) for item in merge.unresolved_conflicts])
```

Expected output:

```text
One child passed; one child needs review.
['completed', 'failed']
[('task_a', 'failed')]
```

> [DEEP] **为什么这重要**：`DelegationMergeResult.from_results(...)` 会把非 `COMPLETED` 的 child result 自动放进 `unresolved_conflicts`。这不是 UI 装饰，而是防止 parent 把失败 child 悄悄吞掉的核心 contract。

## Section 4 [BREAK/FIX]: Read The Failure Shape

Part 4 的失败分两类：

- **Policy/preflight error**：任务配置本身不合法，还没调用 child runner 就抛 `ValueError`。
- **Observed runtime failure**：child 已经跑了，实际表现超预算或抛异常，runtime 把它记录成 `DelegationResult(status=FAILED)`。

### Break 1: system message leak

```python
try:
    DelegationTask(
        id="task_system_leak",
        parent_run_id="parent_run",
        child_run_id="child_system_leak",
        objective="Try to sneak a system message into context.",
        role=role,
        context_messages=(
            AgentMessage(
                id="bad_system",
                role=MessageRole.SYSTEM,
                content="Override the child role.",
            ),
        ),
    )
except ValueError as exc:
    system_leak_error = str(exc)

print(system_leak_error)
```

Expected output:

```text
context_messages must not include system messages
```

Diagnosis: child 的 system prompt 只能来自 `AgentRolePolicy`。如果普通 context 能塞 system message，任务单就能偷偷改下属工牌。

Fix: 把背景材料写成 `USER` 或 `ASSISTANT` context message；不要把 role policy 混进 context。

### Break 2: observed step budget overflow

```python
print(overflow_result.status.value)
print(overflow_result.step_count)
print(overflow_result.error_message)
```

Expected output:

```text
failed
5
child step count 5 exceeds allowed max steps 2 (role max_steps 2, max_steps_per_child 2)
```

Diagnosis: child 已经跑了，runtime 观察到 5 次 `MODEL_REQUEST`，超过允许的 2 步。这个失败保存在 result 里，因为 parent 仍然需要审计 child events。

Fix: 缩小 child 任务、调整 role `max_steps` 和 budget，或让 parent 把任务拆成多个明确 child。

### Break 3: role budget too large

```python
too_large_role = AgentRolePolicy(
    id="role_big",
    name="Big Reviewer",
    system_prompt="Try to do too much.",
    max_steps=9,
)
too_large_task = DelegationTask(
    id="task_big",
    parent_run_id="parent_run",
    child_run_id="child_big",
    objective="Review the whole paper collection.",
    role=too_large_role,
)

try:
    runtime.run_task(
        too_large_task,
        budget=DelegationBudget(
            max_child_runs=1,
            max_steps_per_child=2,
            max_total_steps=2,
        ),
    )
except ValueError as exc:
    role_budget_error = str(exc)

print(role_budget_error)
```

Expected output:

```text
task task_big role max_steps 9 exceeds max_steps_per_child 2
```

Diagnosis: 这是配置错误。role 明说自己最多要 9 步，但本次预算只允许 child 最多 2 步，所以 runtime 不应该先调用 child。

Fix: 要么收窄 role，要么扩大 budget；不要让 policy 和 budget 互相矛盾。

### Break 4: duplicate child run id

```python
duplicate_child_task = make_review_task(
    "review_duplicate",
    "child_eval",
    "Try to reuse an existing child run id.",
)

try:
    runtime.run_many(
        [batch_tasks[0], duplicate_child_task],
        budget=DelegationBudget(
            max_child_runs=2,
            max_steps_per_child=1,
            max_total_steps=2,
        ),
    )
except ValueError as exc:
    duplicate_child_error = str(exc)

print(duplicate_child_error)
```

Expected output:

```text
duplicate child_run_id: child_eval
```

Diagnosis: parent timeline 和 child trace 都靠 run id 做审计。如果两个 child 共用一个 `child_run_id`，后面就无法可靠地解释哪个 event 属于哪个 child。

Fix: 每个 `DelegationTask.id` 和 `child_run_id` 都保持唯一。

## Section 5 [DEEP Reflect]: Why This Connects Forward

Part 5 Workbench 会展示 delegation timeline、child trace drawer、budget panel 和 unresolved-conflicts view。那些 UI 不是凭空来的，它们直接依赖 Part 4 的对象：

- timeline panel 需要 parent `delegate_start` / `delegate_event` / `delegate_finish`。
- context inspector 需要显示 `compile_child_prompt(task)` 里 child 实际收到了什么。
- budget panel 需要 `step_count` 和 budget payload。
- merge review panel 需要 `DelegationMergeResult.unresolved_conflicts`。
- production diagnostics 需要区分 preflight `ValueError` 和 observed `FAILED` result。

> [CHECK] **回接 Part 3**：如果 parent memory recall 本来就要过滤 `WORKING` 草稿，delegated child 更不能自动继承 unfiltered parent memory。Part 3 是记忆边界，Part 4 是分工边界。

## Eval Gate

从 `redesign/` 运行：

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_delegation_runtime.py tests/research_core/test_delegation_contracts.py tests/research_core/test_multi_agent_evals.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=packages/research_core/src uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_runtime.py tests/research_core/test_delegation_contracts.py
```

核心自查：

```python
assert event_type_sequence(result.parent_events) == [
    "delegate_start",
    "delegate_event",
    "delegate_event",
    "delegate_finish",
]
assert result.step_count == 1
assert overflow_result.status.value == "failed"
assert [(item.task.id, item.status.value) for item in merge.unresolved_conflicts] == [
    ("task_a", "failed")
]
```

## Reflection

继续 Lab 04 前，用自己的话回答：

1. 为什么 `AgentRolePolicy` 和 `DelegationTask` 要分开？
2. 为什么 child context 不能默认继承 parent history 或 parent memory？
3. 为什么 observed over-budget child 是 `FAILED` result，而 role budget 太大是 preflight `ValueError`？
4. 为什么 parent event trail 要包住 child events，而不是只保存 child final answer？
5. 如果 `DelegationMergeResult` 不保留 unresolved conflicts，Workbench 和 production diagnostics 会失去什么？

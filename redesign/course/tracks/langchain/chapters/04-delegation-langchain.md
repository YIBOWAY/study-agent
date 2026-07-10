# Part 4: Delegation（LangChain 轨）

> 接 Part 3。notebook 与 skill 管“自己记什么 / 开什么包”；Part 4 管**把小任务外包给 child 但不失控**：child 看见什么、花了多少步、失败是否留在 parent 审计面。主课 Part 4 可对照，但**本轨不 import** `research_core`。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：`DelegationCoordinator` 串行派工：`WorkerRole` + `WorkerTask` + `WorkerBudget` → `WorkerResult` / `MergeResult`。
- **你会解释**：为什么 child prompt 只含 objective + allowed context；为什么 budget 按 child `model_request` 计数；为什么 merge 不吞 failed worker。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_delegation.py -q`（离线）。
- **诚实边界**：不自动 enforce skill/memory allowlist；提供 `filter_tools_for_role` helper。不依赖 LangGraph。

## 与 handwritten 对照

| Handwritten (`research_core`) | 本轨 (`langchain_course`) |
| --- | --- |
| `AgentRolePolicy` | `WorkerRole` |
| `DelegationTask` | `WorkerTask` |
| `DelegationBudget` | `WorkerBudget` |
| `DelegationRuntime` | `DelegationCoordinator` |
| `DelegationResult` / merge | `WorkerResult` / `MergeResult` |
| parent `delegate_*` events | parent `AgentStep`：`delegate_start` / `delegate_finish` |
| `compile_child_prompt` | 同名 |
| `filter_tools_for_role` | 同名（helper，非静默魔法） |

> [DD] **为何 sequential、不用 LangGraph supervisor？** 先把 context 隔离、预算计数、失败可见教清楚；真实并发/图编排只会放大未定义边界。LC 轨 Parts 1–7 仍约定不依赖 LangGraph。

## Section 1：问题钩子

研究员说：

> 一个 reviewer 只查 citation links，另一个只查 evaluation risks，再合并。

三个坑立刻出现：

1. child 继承了 parent 私有推理 / 未确认 memory
2. child 多轮 model 请求，parent 只看到 “done”
3. 一个 child 失败，merge 只拼成功摘要，看起来一切正常

```text
Parent
  -> WorkerTask(role, objective, context_messages)
  -> DelegationCoordinator.run_task / run_many
       emit delegate_start
       runner(task, filtered_tools) -> AgentRunResult
       count model_request steps vs budget
       emit delegate_finish
  -> MergeResult(decisions, unresolved_conflicts, summary)
```

## Section 2 [BUILD]：编译 child prompt（隔离）

```bash
uv run python
```

```python
from langchain_course.delegation import WorkerRole, WorkerTask, compile_child_prompt

role = WorkerRole(
    name="citation_reviewer",
    system_prompt="Check citation links only.",
    max_steps=2,
    tool_names=("echo",),
)
task = WorkerTask(
    task_id="t_cite",
    role=role,
    objective="Verify claim links mention paper_1.",
    context_messages=(
        "Claim: RAG eval needs citation grounding.",
        "Evidence quote mentions citation grounding.",
    ),
)
prompt = compile_child_prompt(task)
print(prompt)
assert "Objective: Verify claim links mention paper_1." in prompt
assert "Allowed context:" in prompt
assert "1. Claim: RAG eval needs citation grounding." in prompt
assert "Do not invent parent-private history." in prompt
assert "secret parent chain-of-thought" not in prompt
```

> [CHECK] child **只**应看到你放进 `context_messages` 的材料。parent 其它历史默认不传。

## Section 3 [BUILD]：单 worker + parent trail

```python
from langchain_course.delegation import (
    DelegationCoordinator,
    WorkerBudget,
    make_plain_agent_result,
    scripted_runner,
)

budget = WorkerBudget(max_workers=2, max_steps_per_worker=4, max_total_steps=8)
coord = DelegationCoordinator()
runner = scripted_runner(
    {"t_cite": make_plain_agent_result("links ok for paper_1", model_requests=1)}
)
result = coord.run_task(task, budget, runner=runner, tools=())
print(result.status, result.final_text, result.step_count)
print(coord.parent_step_kinds())
assert result.status == "completed"
assert result.step_count == 1
assert coord.parent_step_kinds() == ["delegate_start", "delegate_finish"]
```

> [TRAP] **`step_count` = child `model_request` 次数**，不是全部 `AgentStep` 长度。`model_response` / `tool_*` 进审计，但不按本轨预算扣步。

## Section 4 [BUILD]：run_many + merge 冲突可见

```python
from langchain_course.delegation import WorkerTask

tasks = [
    WorkerTask(
        task_id="t_cite",
        role=role,
        objective="Check citations.",
        context_messages=("paper_1 quote...",),
    ),
    WorkerTask(
        task_id="t_risk",
        role=WorkerRole(
            name="risk_reviewer",
            system_prompt="List evaluation risks only.",
            max_steps=2,
        ),
        objective="List eval risks.",
        context_messages=("Hallucinated citations are a risk.",),
    ),
]
runner = scripted_runner(
    {
        "t_cite": make_plain_agent_result("citations grounded", model_requests=1),
        "t_risk": make_plain_agent_result("risk: missing metrics", model_requests=1),
    }
)
coord2 = DelegationCoordinator()
merged = coord2.run_many(tasks, budget, runner=runner)
print(merged.summary)
print(merged.decisions)
assert len(merged.decisions) == 2
assert merged.unresolved_conflicts == ()
```

失败 worker 进入 `unresolved_conflicts`，**不会**被静默丢掉：

```python
def boom_runner(task, tools):
    raise RuntimeError("child crashed")

coord3 = DelegationCoordinator()
failed = coord3.run_task(tasks[0], budget, runner=boom_runner)
assert failed.status == "failed"
assert "RuntimeError" in failed.error_message
merged_fail = coord3.run_many(tasks[:1], budget, runner=boom_runner)
assert merged_fail.unresolved_conflicts
assert "t_cite" in merged_fail.unresolved_conflicts[0]
```

## Section 5 [BUILD]：tool filter helper

```python
from langchain_course.tools_echo import echo, add
from langchain_course.delegation import filter_tools_for_role

role_echo_only = WorkerRole(
    name="echoer",
    system_prompt="Use echo only.",
    tool_names=("echo",),
)
filtered = filter_tools_for_role(role_echo_only, [echo, add])
assert [t.name for t in filtered] == ["echo"]

# 空 tool_names = 不过滤（返回全部传入 tools）
role_all = WorkerRole(name="all", system_prompt="all tools", tool_names=())
assert [t.name for t in filter_tools_for_role(role_all, [echo, add])] == ["echo", "add"]
```

> [DD] **诚实边界**：`run_task` 会对传入的 `tools` 调用 `filter_tools_for_role`。skill/memory allowlist **不**自动 enforce——与主课 Part 4 同一课。工牌上的声明不等于 runtime 魔法。

## Section 6 [BREAK / FIX]

1. `role.max_steps > budget.max_steps_per_worker` → `DelegationError`（跑之前）
2. `len(tasks) > budget.max_workers` → `DelegationError`
3. scripted child `model_requests` 超过 cap → `WorkerResult.status == "failed"`，`error_message` 含 `budget exceeded`

```python
from langchain_course.delegation import DelegationError

tight = WorkerBudget(max_workers=1, max_steps_per_worker=1, max_total_steps=1)
big_role = WorkerRole(name="x", system_prompt="x", max_steps=5)
try:
    DelegationCoordinator().run_task(
        WorkerTask(task_id="t", role=big_role, objective="o"),
        tight,
        runner=scripted_runner({"t": make_plain_agent_result("x")}),
    )
except DelegationError as exc:
    assert "max_steps" in str(exc)
```

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_delegation.py -q
```

## Reflection

1. 若要把 Part 3 的 pinned memory 给 child，正确做法是写进 `context_messages`，还是共享整个 `Notebook` 对象？为什么？
2. merge 保留 `unresolved_conflicts` 对产品 UI 意味着什么？
3. 本轨不用 LangGraph supervisor 图，教学上换来了什么透明度？

## 下一步

- Lab：[labs/04-delegation-lab.md](../labs/04-delegation-lab.md)
- Solution：[solutions/04-delegation-solution.md](../solutions/04-delegation-solution.md)

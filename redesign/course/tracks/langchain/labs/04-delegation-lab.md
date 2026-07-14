# Lab 04 — Delegation（LangChain 轨）

接 Chapter 04。练习 child context 隔离、预算计数、merge 冲突可见。

预计时间：45–60 分钟。

## Setup

```bash
cd redesign
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_course.delegation import (
    DelegationCoordinator,
    DelegationError,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    compile_child_prompt,
    filter_tools_for_role,
    make_plain_agent_result,
    scripted_runner,
)
from langchain_course.tools_echo import add, echo
```

## Exercise 1 (L1 Follow): Child prompt isolation

```python
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
        "Claim text about citation grounding.",
        "Quote from paper_1.",
    ),
)
prompt = compile_child_prompt(task)
assert "Objective:" in prompt
assert "Allowed context:" in prompt
assert "Quote from paper_1." in prompt
# 故意不把 parent 私货放进 context_messages → prompt 中不应出现
assert "parent secret CoT" not in prompt
```

## Exercise 2 (L1 Follow): Single task trail

```python
budget = WorkerBudget(max_workers=2, max_steps_per_worker=4, max_total_steps=8)
coord = DelegationCoordinator()
runner = scripted_runner(
    {"t_cite": make_plain_agent_result("links ok", model_requests=1)}
)
result = coord.run_task(task, budget, runner=runner)
assert result.status == "completed"
assert result.final_text == "links ok"
assert result.step_count == 1
assert coord.parent_step_kinds() == ["delegate_start", "delegate_finish"]
rec = result.to_record()
assert rec["task_id"] == "t_cite"
assert rec["status"] == "completed"
```

## Exercise 3 (L2 Modify): run_many + tool filter + one failure

1. 再建 `t_risk` worker（不同 `WorkerRole`），`scripted_runner` 返回两条 completed；`run_many` 后 `len(merged.decisions) == 2`，`unresolved_conflicts == ()`。
2. 对 `filter_tools_for_role(role, [echo, add])` 断言只剩 `echo`。
3. 换一个会 `raise RuntimeError("boom")` 的 runner，对单 task `run_task`：`status == "failed"`，且 parent kinds 仍含 `delegate_start` 与 `delegate_finish`。
4. 用 `RunnableLambda` 创建 citation/risk 两个只读 worker，通过
   `build_parallel_worker_runnable` 同时处理一个 question。比较它和 coordinator：
   前者返回 dict，后者额外带 budget、status、parent trail 和 conflicts。

## Exercise 4 (L3 Design): Budget edges

1. `role.max_steps=5` 且 `budget.max_steps_per_worker=1` → 捕获 `DelegationError`。
2. `make_plain_agent_result(..., model_requests=3)` 且 cap 为 1 → `WorkerResult.status == "failed"`，`error_message` 含 `budget exceeded`。
3. 写 3–5 句：若要把 Part 3 的 pinned memory 交给 child，为什么应 **复制进 `context_messages`**，而不是共享整个 `Notebook`？这与 skill/memory allowlist **不自动 enforce** 的诚实边界如何一致？
4. 哪些 worker 可以安全放进 `RunnableParallel`？列出共享副作用、总预算和
   失败回滚三个反例。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_delegation.py -q
```

## Optional live（非门禁）

可用 `run_tool_calling_agent` 作为 runner 调用 DeepSeek；仍只断言结构（status / parent steps / 非空 final_text），不要全文相等。

## 对照

Solution：[../solutions/04-delegation-solution.md](../solutions/04-delegation-solution.md)

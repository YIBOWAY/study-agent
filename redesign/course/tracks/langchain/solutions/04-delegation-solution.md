# Solution 04 — Delegation（LangChain 轨）

## 参考要点

### L1 Child prompt

- `compile_child_prompt` 固定结构：`Objective` + 可选 `Allowed context` 编号列表 + “不要编造 parent-private history”。
- 隔离靠**调用方不传**，不是靠模型自觉。

### L1 Single task trail

- parent 只追加 `delegate_start` / `delegate_finish`（payload 含 task_id、role、status 等）。
- `step_count` = child steps 里 `kind == "model_request"` 的数量。
- `make_plain_agent_result(text, model_requests=n)` 便于离线构造。

### L2 run_many + filter + failure

```python
from langchain_course.delegation import (
    DelegationCoordinator,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    filter_tools_for_role,
    make_plain_agent_result,
    scripted_runner,
)
from langchain_course.tools_echo import add, echo

budget = WorkerBudget(max_workers=3, max_steps_per_worker=4, max_total_steps=12)
cite = WorkerRole(
    name="citation_reviewer",
    system_prompt="Check citations.",
    max_steps=2,
    tool_names=("echo",),
)
risk = WorkerRole(
    name="risk_reviewer",
    system_prompt="List risks.",
    max_steps=2,
)
tasks = [
    WorkerTask(task_id="t_cite", role=cite, objective="Check citations.", context_messages=("q1",)),
    WorkerTask(task_id="t_risk", role=risk, objective="List risks.", context_messages=("q2",)),
]
runner = scripted_runner(
    {
        "t_cite": make_plain_agent_result("citations ok", model_requests=1),
        "t_risk": make_plain_agent_result("risk: missing metrics", model_requests=1),
    }
)
merged = DelegationCoordinator().run_many(tasks, budget, runner=runner)
assert len(merged.decisions) == 2
assert merged.unresolved_conflicts == ()
assert "completed" in merged.summary

assert [t.name for t in filter_tools_for_role(cite, [echo, add])] == ["echo"]

def boom(task, tools):
    raise RuntimeError("boom")

coord = DelegationCoordinator()
failed = coord.run_task(tasks[0], budget, runner=boom)
assert failed.status == "failed"
assert "RuntimeError" in failed.error_message
assert coord.parent_step_kinds() == ["delegate_start", "delegate_finish"]
```

### L3 Budget edges

```python
from langchain_course.delegation import (
    DelegationCoordinator,
    DelegationError,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    make_plain_agent_result,
    scripted_runner,
)

tight = WorkerBudget(max_workers=1, max_steps_per_worker=1, max_total_steps=1)
big = WorkerRole(name="x", system_prompt="x", max_steps=5)
try:
    DelegationCoordinator().run_task(
        WorkerTask(task_id="t", role=big, objective="o"),
        tight,
        runner=scripted_runner({"t": make_plain_agent_result("x")}),
    )
    raise AssertionError("expected DelegationError")
except DelegationError as exc:
    assert "max_steps" in str(exc)

over = DelegationCoordinator().run_task(
    WorkerTask(
        task_id="t2",
        role=WorkerRole(name="y", system_prompt="y", max_steps=1),
        objective="o",
    ),
    tight,
    runner=scripted_runner(
        {"t2": make_plain_agent_result("too many", model_requests=3)}
    ),
)
assert over.status == "failed"
assert "budget exceeded" in over.error_message
```

**设计讨论参考**：把 pinned memory **复制**进 `context_messages`，child 得到的是一次性快照，parent 可审计“到底泄露了哪些句子”。共享整个 `Notebook` 等于默许 child 任意 recall，与 “skill/memory allowlist 不自动 enforce、由调用方显式编译 context” 的诚实边界冲突。

## 与 handwritten 的差异（有意）

- 不自动把每个 child event 包装成 parent `delegate_event`；本轨 parent trail 聚焦 start/finish 信封 + `WorkerResult.steps` 内嵌。
- runner 是 `(task, tools) -> AgentRunResult` 协议，便于 scripted 与 `run_tool_calling_agent` 互换。
- 类型名 `Worker*` 强调教学角色，避免与产品 `Delegation*` 类型缠在一起。

## 常见错误

1. 用 `len(result.steps)` 当 budget → 应用 `model_request` 计数。
2. 以为 `tool_names=()` 表示“禁用所有工具” → 空 tuple 表示不过滤（返回全部传入 tools）。
3. merge 只读 `summary` 字符串 → 必须检查 `unresolved_conflicts`。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_delegation.py -q
```

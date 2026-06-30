# Lab 07: Production Readiness

## Goal

这个 lab 会带你亲手跑四件事：

1. 用 `RunDiagnostics` 总结一小段 `RunEvent` trajectory。
2. 用 `JsonlRunEventStore` 写入和读回 events。
3. 用 `ApprovalPolicy` 和 `SandboxPolicy` 评估 allow、deny、review 和 blocked decisions。
4. 故意触发一次 policy failure，观察 contract 怎样拒绝坏输入。

预计时间：45 到 60 分钟。

## Setup

所有命令默认从 `redesign/` 运行：

```bash
cd redesign
```

先跑 focused tests：

```bash
uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
```

你应该看到全部通过。

## Exercise 1: Summarize A Run Trajectory

打开 Python shell：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

粘贴：

```python
from research_core.production import RunDiagnostics
from research_core.runtime.events import RunEvent, RunEventType

events = (
    RunEvent(
        id="evt_1",
        run_id="run_7",
        type=RunEventType.MODEL_REQUEST,
        payload={"step": "plan"},
    ),
    RunEvent(
        id="evt_2",
        run_id="run_7",
        type=RunEventType.TOOL_CALL,
        payload={"tool": "retriever.search"},
    ),
    RunEvent(
        id="evt_3",
        run_id="run_7",
        type=RunEventType.ERROR,
        payload={
            "step": "retrieve",
            "error": {"kind": "tool_error", "message": "fixture missing"},
        },
    ),
    RunEvent(
        id="evt_4",
        run_id="run_7",
        type=RunEventType.EVAL_RESULT,
        payload={"metric": "has_citation", "passed": False},
    ),
)

diagnostics = RunDiagnostics.from_events(events)

print(diagnostics.to_record())
```

自查：

```python
assert diagnostics.run_id == "run_7"
assert diagnostics.event_count == 4
assert diagnostics.event_type_counts == {
    "model_request": 1,
    "tool_call": 1,
    "eval_result": 1,
    "error": 1,
}
assert diagnostics.error_summaries[0]["kind"] == "tool_error"
assert diagnostics.error_summaries[0]["message"] == "fixture missing"
```

## Exercise 2: Write And Read Events

还在同一个 shell，粘贴：

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.production import JsonlRunEventStore

tmp = TemporaryDirectory()
path = Path(tmp.name) / "runs" / "events.jsonl"

store = JsonlRunEventStore(path)
store.append_many(events)

print(path.exists())
print(store.list_run_ids())
print([event.id for event in store.read_run("run_7")])
print(store.read_run("missing"))
```

自查：

```python
assert path.exists() is True
assert store.list_run_ids() == ("run_7",)
assert [event.id for event in store.read_run("run_7")] == [
    "evt_1",
    "evt_2",
    "evt_3",
    "evt_4",
]
assert store.read_run("missing") == ()
```

## Exercise 3: Evaluate Approval And Sandbox Decisions

还在同一个 shell，粘贴：

```python
from pathlib import Path

from research_core.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    SandboxPolicy,
)

approval = ApprovalPolicy(
    default_mode=ApprovalMode.REQUIRE_APPROVAL,
    default_reason="Unknown tool needs a human check.",
    rules=(
        ApprovalRule(
            tool_name_pattern="retriever.*",
            mode=ApprovalMode.ALLOW,
            reason="Read-only retrieval is allowed.",
        ),
        ApprovalRule(
            tool_name_pattern="shell.*",
            mode=ApprovalMode.DENY,
            reason="Shell commands are blocked in this lesson.",
        ),
    ),
)

allowed = approval.decide("retriever.search")
denied = approval.decide("shell.exec")
review = approval.decide("email.send")

print(allowed.to_record())
print(denied.to_record())
print(review.to_record())

workspace = Path("tmp/course07-workspace")
sandbox = SandboxPolicy(
    readable_paths=(workspace,),
    writable_paths=(workspace / "outputs",),
    blocked_paths=(workspace / "secrets",),
    allow_network=False,
    max_runtime_seconds=15,
)

read_decision = sandbox.decide_path(workspace / "notes.md", access="read")
write_decision = sandbox.decide_path(workspace / "outputs/report.md", access="write")
secret_decision = sandbox.decide_path(workspace / "secrets/token.txt", access="read")
network_decision = sandbox.network_decision()

print(read_decision.allowed, read_decision.reason)
print(write_decision.allowed, write_decision.reason)
print(secret_decision.allowed, secret_decision.reason)
print(network_decision.allowed, network_decision.reason)
```

自查：

```python
assert allowed.mode is ApprovalMode.ALLOW
assert denied.mode is ApprovalMode.DENY
assert review.requires_review is True
assert read_decision.allowed is True
assert write_decision.allowed is True
assert secret_decision.allowed is False
assert network_decision.allowed is False
```

## Exercise 4: Trigger One Deliberate Failure

故意传入一个 sandbox 不认识的 access name：

```python
try:
    sandbox.decide_path(workspace / "script.sh", access="execute")
except ValueError as exc:
    print(type(exc).__name__, str(exc))
else:
    raise AssertionError("Expected invalid access to fail")
```

你应该看到：

```text
ValueError access must be one of: read, write
```

自查：

```python
try:
    sandbox.decide_path(workspace / "script.sh", access="execute")
except ValueError as exc:
    assert "access must be one of" in str(exc)
else:
    raise AssertionError("Expected invalid access to fail")
```

## Reflection

做完以后，回答：

1. `RunDiagnostics` 为什么要拒绝空 event list 或混合 run_id？
2. `JsonlRunEventStore` 的 append/read contract 和数据库有什么不同？
3. 为什么 `email.send` 默认是 `require_approval`，不是 allow 或 deny？
4. 为什么 blocked path 要比 readable/writable path 优先？
5. Exercise 4 的失败为什么是好事？

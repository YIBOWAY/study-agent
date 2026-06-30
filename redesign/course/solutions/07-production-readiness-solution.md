# Solution 07: Production Readiness

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 Python snippets 默认从 `redesign/` 运行。

## Focused Test Check

```bash
uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
```

期望结果：

```text
11 passed
```

如果数量未来增加，以实际测试数为准；关键是 focused production-readiness tests 必须全部通过。

## Exercise 1 Solution

Shell:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

Python:

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

assert diagnostics.to_record() == {
    "run_id": "run_7",
    "event_count": 4,
    "event_type_counts": {
        "model_request": 1,
        "tool_call": 1,
        "eval_result": 1,
        "error": 1,
    },
    "error_summaries": [
        {
            "event_id": "evt_3",
            "step": "retrieve",
            "kind": "tool_error",
            "message": "fixture missing",
        }
    ],
}
```

Expected print shape:

```text
{'run_id': 'run_7', 'event_count': 4, 'event_type_counts': {'model_request': 1, 'tool_call': 1, 'eval_result': 1, 'error': 1}, 'error_summaries': [{'event_id': 'evt_3', 'step': 'retrieve', 'kind': 'tool_error', 'message': 'fixture missing'}]}
```

What this proves:

- the run has one stable `run_id`;
- the trajectory can be summarized without reading every payload by hand;
- the error event keeps the useful failure detail: step, kind, and message.

## Exercise 2 Solution

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.production import JsonlRunEventStore

tmp = TemporaryDirectory()
path = Path(tmp.name) / "runs" / "events.jsonl"

store = JsonlRunEventStore(path)
store.append_many(events)

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

Expected prints:

```text
True
('run_7',)
['evt_1', 'evt_2', 'evt_3', 'evt_4']
()
```

What this proves:

- the store creates the parent directory;
- events are read back in append order;
- missing run IDs return an empty tuple instead of fabricating data.

## Exercise 3 Solution

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

assert allowed.to_record() == {
    "subject": "retriever.search",
    "mode": "allow",
    "reason": "Read-only retrieval is allowed.",
    "matched_rule": "retriever.*",
}
assert denied.to_record() == {
    "subject": "shell.exec",
    "mode": "deny",
    "reason": "Shell commands are blocked in this lesson.",
    "matched_rule": "shell.*",
}
assert review.to_record() == {
    "subject": "email.send",
    "mode": "require_approval",
    "reason": "Unknown tool needs a human check.",
    "matched_rule": "",
}

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

assert read_decision.allowed is True
assert read_decision.reason == "path is allowed for read"
assert write_decision.allowed is True
assert write_decision.reason == "path is allowed for write"
assert secret_decision.allowed is False
assert secret_decision.reason == "path is blocked by sandbox policy"
assert network_decision.to_record() == {
    "subject": "network",
    "allowed": False,
    "reason": "network access is disabled",
}
```

Expected approval prints:

```text
{'subject': 'retriever.search', 'mode': 'allow', 'reason': 'Read-only retrieval is allowed.', 'matched_rule': 'retriever.*'}
{'subject': 'shell.exec', 'mode': 'deny', 'reason': 'Shell commands are blocked in this lesson.', 'matched_rule': 'shell.*'}
{'subject': 'email.send', 'mode': 'require_approval', 'reason': 'Unknown tool needs a human check.', 'matched_rule': ''}
```

Expected sandbox prints:

```text
True path is allowed for read
True path is allowed for write
False path is blocked by sandbox policy
False network access is disabled
```

What this proves:

- approval answers tool-subject questions;
- sandbox answers path and network boundary questions;
- unknown tools can require review without being silently allowed.

## Exercise 4 Solution

```python
try:
    sandbox.decide_path(workspace / "script.sh", access="execute")
except ValueError as exc:
    assert str(exc) == "access must be one of: read, write"
else:
    raise AssertionError("Expected invalid access to fail")
```

Expected print:

```text
ValueError access must be one of: read, write
```

What went wrong:

`SandboxPolicy.decide_path()` only accepts two access names: `read` and `write`.
The lab passed `execute`, which is not part of the contract.

That failure is intentional. The policy should not guess whether execute means read, write, shell, or something else. A production boundary is safer when unknown actions fail with a clear error before any tool runs.

## Final Takeaway

The important lesson is:

```text
Production readiness starts with inspectable local contracts.
```

Once diagnostics, event persistence, approval decisions, sandbox decisions, and focused tests are stable offline, future infrastructure can wrap them. Without those contracts, infrastructure only makes failures harder to understand.

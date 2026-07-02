# Solution 07: Production Readiness

这份 solution 用来校准理解。请先自己完成 Lab 07，再回来对答案。尤其是 L3：这里给的是一个**参考设计**，不是唯一正确答案。任何满足相同不变量的设计都算对：单 run diagnostics、JSONL replay 保序、审批规则可解释、secrets 被挡、network 显式关闭。

所有 Python snippets 默认从 `redesign/` 运行。Part 7 只 import `research_core.production` 和 `research_core.runtime`，所以这个命令就够：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

也可以先确认 focused production tests 是绿的：

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
```

期望结果：

```text
11 passed
```

数量未来可能增加，以实际测试数为准；关键是 focused production-readiness tests 必须全绿。

## L1 Follow Solution

L1 只做最小闭环：同一段 `run_7` events 先生成 diagnostics，再写入 JSONL 读回，最后跑 approval/sandbox decisions。这里的输出只有一行，因为真正的检查在 `assert` 里。

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    JsonlRunEventStore,
    RunDiagnostics,
    SandboxPolicy,
)
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

l1_tmp = TemporaryDirectory()
path = Path(l1_tmp.name) / "runs" / "events.jsonl"
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
assert review.requires_review is True

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

print("L1 solution passed")
```

Expected output:

```text
L1 solution passed
```

What This Proves:

- `RunDiagnostics` 摘的是一整个 run，而不是孤立日志行：它保留 `run_id`、event 数量、event type 计数和错误摘要。
- `JsonlRunEventStore` 不是数据库，但已经能完成课程需要的最小 audit trail：append、列出 run id、按 run id 原顺序 replay。
- Approval 和 sandbox 是两道不同的闸：一个回答“这个工具动作要不要人审”，一个回答“这个路径/网络边界能不能碰”。

Why This Design:

- L1 把四件事放在同一段代码里，是为了让你看到 production readiness 的最小闭环：先有轨迹，再有摘要，再能回放，最后才谈执行边界。
- `email.send` 没有被默默允许，而是走 default `require_approval`。这比“未知动作先放行”更适合本课程的本地安全台。
- `blocked_paths` 比 readable/writable roots 更强：secrets 即使在 workspace 下面，也必须被显式挡住。

## L2 Modify/Break-Fix Solution

L2 分两类：先改正常输入，看 diagnostics 和 policy decision 如何变化；再逐个打破边界，确认错误信息是哪道护栏在说话。

```python
modified_events = events + (
    RunEvent(
        id="evt_5",
        run_id="run_7",
        type=RunEventType.TOOL_RESULT,
        payload={"tool": "retriever.search", "items": 0},
    ),
)

modified = RunDiagnostics.from_events(modified_events)
modified_record = modified.to_record()

assert modified.event_count == 5
assert modified_record["event_type_counts"] == {
    "model_request": 1,
    "tool_call": 1,
    "tool_result": 1,
    "eval_result": 1,
    "error": 1,
}
assert modified.error_summaries[0]["message"] == "fixture missing"

strict_approval = ApprovalPolicy(
    default_mode=ApprovalMode.REQUIRE_APPROVAL,
    default_reason="Unknown tool needs a human check.",
    rules=(
        ApprovalRule(
            tool_name_pattern="retriever.*",
            mode=ApprovalMode.ALLOW,
            reason="Read-only retrieval is allowed.",
        ),
        ApprovalRule(
            tool_name_pattern="email.*",
            mode=ApprovalMode.DENY,
            reason="Outbound email is blocked in the lab.",
        ),
        ApprovalRule(
            tool_name_pattern="shell.*",
            mode=ApprovalMode.DENY,
            reason="Shell commands are blocked in this lesson.",
        ),
    ),
)

email_decision = strict_approval.decide("email.send")
assert email_decision.mode is ApprovalMode.DENY
assert email_decision.reason == "Outbound email is blocked in the lab."
assert email_decision.matched_rule == "email.*"

network_sandbox = SandboxPolicy(
    readable_paths=(workspace,),
    writable_paths=(workspace / "outputs",),
    blocked_paths=(workspace / "secrets",),
    allow_network=True,
    max_runtime_seconds=15,
)
open_network = network_sandbox.network_decision()
assert open_network.allowed is True
assert open_network.reason == "network access is enabled"

try:
    RunDiagnostics.from_events(())
except ValueError as exc:
    assert str(exc) == "events must not be empty"
else:
    raise AssertionError("Expected empty events to fail")

mixed_events = (
    events[0],
    RunEvent(
        id="evt_other",
        run_id="run_other",
        type=RunEventType.MODEL_RESPONSE,
        payload={"text": "other run"},
    ),
)
try:
    RunDiagnostics.from_events(mixed_events)
except ValueError as exc:
    assert str(exc) == "events must belong to one run_id"
else:
    raise AssertionError("Expected mixed run IDs to fail")

broken_tmp = TemporaryDirectory()
broken_path = Path(broken_tmp.name) / "events.jsonl"
broken_path.write_text('{"schema_version": "wrong", "event": {}}\n', encoding="utf-8")
broken_store = JsonlRunEventStore(broken_path)
try:
    broken_store.read_all()
except ValueError as exc:
    assert str(exc) == "unsupported event log schema at line 1"
else:
    raise AssertionError("Expected invalid event log schema to fail")

try:
    approval.decide(" ")
except ValueError as exc:
    assert str(exc) == "subject must not be empty"
else:
    raise AssertionError("Expected blank approval subject to fail")

try:
    sandbox.decide_path(workspace / "script.sh", access="execute")
except ValueError as exc:
    assert str(exc) == "access must be one of: read, write"
else:
    raise AssertionError("Expected invalid sandbox access to fail")

assert secret_decision.allowed is False
assert secret_decision.reason == "path is blocked by sandbox policy"
assert network_decision.allowed is False
assert network_decision.reason == "network access is disabled"

print("L2 solution passed")
```

Expected output:

```text
L2 solution passed
```

What This Proves:

- 追加 `tool_result` 后，diagnostics 的 `event_count` 和 `event_type_counts` 会随真实 trajectory 改变；错误摘要仍然指向原来的 error event。
- 加入 `email.*` deny rule 后，`email.send` 不再走 default review，而是命中更明确的拒绝规则。
- 七个 break/fix 覆盖两类边界：异常型坏输入会抛清楚的 `ValueError`，blocked path/network disabled 会返回 `allowed=False` 的 typed decision。

Why This Design:

- 每个异常块都用 `try/except/else` 自校验，是为了让 markdown gate 继续执行整份 solution；未捕获异常只证明“文件中断”，不能教你边界含义。
- `blocked path` 和 `disabled network` 不抛异常，是因为它们代表一次有效的 policy 查询，答案是“拒绝”。这和 schema 错、subject 空、access 不受支持不一样。
- 错误文本逐字断言不是吹毛求疵：生产可诊断性的一部分，就是失败输出能稳定告诉你该回到哪道 contract。

## L3 Design Solution

这是一个**合法的参考设计，不是唯一正确答案**。场景是 R8 Capstone 前的本地 report export rehearsal：助手要读取草稿、导出最终报告，但不能碰 secrets，也不能默认联网。

```python
l3_events = (
    RunEvent(
        id="evt_export_1",
        run_id="run_export",
        type=RunEventType.MODEL_REQUEST,
        payload={"step": "plan_export"},
    ),
    RunEvent(
        id="evt_export_2",
        run_id="run_export",
        type=RunEventType.TOOL_CALL,
        payload={"tool": "retriever.search", "query": "capstone notes"},
    ),
    RunEvent(
        id="evt_export_3",
        run_id="run_export",
        type=RunEventType.TOOL_RESULT,
        payload={"tool": "retriever.search", "items": 3},
    ),
    RunEvent(
        id="evt_export_4",
        run_id="run_export",
        type=RunEventType.TOOL_CALL,
        payload={"tool": "report.export", "target": "outputs/final.md"},
    ),
    RunEvent(
        id="evt_export_5",
        run_id="run_export",
        type=RunEventType.EVAL_RESULT,
        payload={"metric": "report_ready", "passed": True},
    ),
)

l3_diagnostics = RunDiagnostics.from_events(l3_events)
assert len({event.run_id for event in l3_events}) == 1
assert l3_diagnostics.run_id == "run_export"
assert l3_diagnostics.event_count == len(l3_events)
assert l3_diagnostics.to_record()["event_type_counts"] == {
    "model_request": 1,
    "tool_call": 2,
    "tool_result": 1,
    "eval_result": 1,
}
assert l3_diagnostics.error_summaries == ()

l3_tmp = TemporaryDirectory()
l3_store = JsonlRunEventStore(Path(l3_tmp.name) / "events.jsonl")
l3_store.append_many(l3_events)
assert [event.id for event in l3_store.read_run("run_export")] == [
    event.id for event in l3_events
]
assert l3_store.list_run_ids() == ("run_export",)

l3_approval = ApprovalPolicy(
    default_mode=ApprovalMode.REQUIRE_APPROVAL,
    default_reason="Unknown export action needs review.",
    rules=(
        ApprovalRule(
            tool_name_pattern="retriever.*",
            mode=ApprovalMode.ALLOW,
            reason="Read-only retrieval is allowed.",
        ),
        ApprovalRule(
            tool_name_pattern="report.export",
            mode=ApprovalMode.REQUIRE_APPROVAL,
            reason="Report export creates an artifact that a human should review.",
        ),
        ApprovalRule(
            tool_name_pattern="shell.*",
            mode=ApprovalMode.DENY,
            reason="Shell commands are blocked for report export.",
        ),
    ),
)

retriever_decision = l3_approval.decide("retriever.search")
export_decision = l3_approval.decide("report.export")
shell_decision = l3_approval.decide("shell.exec")
unknown_decision = l3_approval.decide("email.send")

assert retriever_decision.mode is ApprovalMode.ALLOW
assert export_decision.requires_review is True
assert export_decision.matched_rule == "report.export"
assert shell_decision.mode is ApprovalMode.DENY
assert unknown_decision.requires_review is True

l3_workspace = Path("tmp/report-export")
l3_sandbox = SandboxPolicy(
    readable_paths=(l3_workspace / "notes",),
    writable_paths=(l3_workspace / "outputs",),
    blocked_paths=(l3_workspace / "secrets",),
    allow_network=False,
    max_runtime_seconds=30,
)

assert l3_sandbox.decide_path(
    l3_workspace / "notes/draft.md",
    access="read",
).allowed is True
assert l3_sandbox.decide_path(
    l3_workspace / "outputs/final.md",
    access="write",
).allowed is True
assert l3_sandbox.decide_path(
    l3_workspace / "secrets/token.txt",
    access="read",
).allowed is False
assert l3_sandbox.network_decision().allowed is False

print("L3 reference design passed")
```

Expected output:

```text
L3 reference design passed
```

What This Proves:

- L3 的 event trail 是一个完整、单一的 `run_export`：可以被 diagnostics 摘要，也可以被 JSONL store 原顺序 replay。
- Approval policy 的三个关键动作都可解释：`retriever.*` allow，`report.export` require approval，`shell.*` deny；未知动作仍走 default review。
- Sandbox policy 把读、写、secrets、network 分开表达：notes 可读、outputs 可写、secrets 被挡、network 关闭。

Why This Design:

- `report.export` 被放在 require approval，而不是 allow，是因为它会产生最终交付物；课程还没有真实发布系统，所以人工 review 是更诚实的边界。
- `retriever.*` 允许，是因为这里把它建模为只读检索；如果未来 retriever 会联网或访问外部账号，policy 必须重新设计。
- L3 不追求“唯一答案”，追求不变量：能保存、读回、解释、审批、阻断，并用 assert 证明这些事发生了。

## Forward Connections

R8 Capstone 不应该只交一份看起来像报告的 markdown。它至少要带上这些 trust evidence：

- saved event log：能 replay 最终 run 的关键轨迹；
- diagnostics summary：能快速看到 event count、event types、error summaries；
- approval/sandbox records：能解释哪些动作被允许、哪些需要 review、哪些被拒绝；
- docs freshness 和 markdown block gate：能证明课程文档和真实 API 没漂；
- readiness checklist：能说明为什么当前系统仍是本地教学/原型边界，而不是云端生产发布。

R7 的意义就是把“能跑”升级成“能复盘、能审计、能挡危险动作”。到了 R8，Capstone 要把这组证据作为最终项目的一部分，而不是事后补一句“应该安全”。

## Final Takeaway

Production readiness 不是先买云服务、接数据库、堆监控面板。对这个 redesign 来说，第一步更朴素也更硬：

```text
If a local run cannot be replayed, diagnosed, approved, and sandboxed, it is not ready to be trusted.
```

先把本地边界做成可执行 contract，再谈更重的生产基础设施。

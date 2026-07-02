# Chapter 07: Production Readiness

## Goal

这一章补上 Phase 7 的生产可用性训练：不是部署云服务，不是接 OAuth，不是上数据库，而是先把 agent run 里最容易出事故的几件事变成清楚、离线、可测试的 contracts。

学完以后，你应该能看懂这条主线：

```text
RunEvent trajectory
  -> RunDiagnostics
  -> JsonlRunEventStore
  -> ApprovalPolicy and SandboxPolicy
  -> focused eval gate
```

预计时间：60 到 75 分钟。

## Before You Start

请先完成：

- `01-agent-kernel-foundations.md`
- `05-workbench-product.md`
- `06-framework-comparisons.md`

这一章不会添加真实 provider、真实网络调用、登录、云资源或数据库。Phase 7 只建立本地生产 readiness 的第一层：看得见、存得住、挡得住。

## The Idea In Plain Language

生产可用性不是“上线前加一堆平台”。

对一个 agent runtime 来说，第一层生产可用性是三句很朴素的问题：

1. 出事以后，我能不能看懂刚才发生了什么？
2. 这次 run 的 event trail 能不能被保存和重放检查？
3. 危险动作能不能在执行前被 policy 拦住？

Phase 7 的答案不是新框架，而是几个小 contract：

| Contract | Plain-language job |
| --- | --- |
| `RunDiagnostics` | 把一串 `RunEvent` 总结成数量、类型和错误摘要 |
| `JsonlRunEventStore` | 把 events 追加写进 JSONL，再按 run_id 读回来 |
| `ApprovalPolicy` | 判断某个 tool subject 是 allow、deny，还是 require approval |
| `SandboxPolicy` | 判断路径和网络访问是否在本地 sandbox 允许范围内 |

这些对象都在 `research_core.production`。它们不 import FastAPI、React、provider SDK 或数据库 client。

## Why Contracts Come Before Infrastructure

很多 production 讨论会太快跳到这些词：

```text
cloud logging, database persistence, OAuth scopes, job queues, dashboards
```

这些以后可能有价值，但初学阶段先不要把问题搞大。

如果本地 contract 都没有，云上只会更难 debug：

- 没有 `RunDiagnostics`，你只会看到“失败了”，但不知道是哪类 event 失败。
- 没有 `JsonlRunEventStore`，你没法保留最小复盘证据。
- 没有 `ApprovalPolicy`，危险 tool 只能靠 prompt 劝它别做。
- 没有 `SandboxPolicy`，文件和网络边界只存在于口头约定。

所以 Phase 7 先做离线版。离线版跑通以后，未来要接真实 log sink、database 或 review UI，才有稳定的 contract 可以包起来。

## Minimal Diagnostics Example

从 `redesign/` 打开 Python shell：

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

你应该能看到：

```text
'event_count': 4
'error_summaries': [{'event_id': 'evt_3', ...}]
```

这不是完整 dashboard。它只是最小可复盘摘要：这个 run 有几个 event，分别是什么类型，错误在哪个 event 里。

## JSONL Event Store

`JsonlRunEventStore` 做一件很窄的事：追加写 event log。

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from research_core.production import JsonlRunEventStore

tmp = TemporaryDirectory()
path = Path(tmp.name) / "runs" / "events.jsonl"

store = JsonlRunEventStore(path)
store.append_many(events)

print(store.list_run_ids())
print([event.id for event in store.read_run("run_7")])
```

你应该看到：

```text
('run_7',)
['evt_1', 'evt_2', 'evt_3', 'evt_4']
```

JSONL 的好处是简单：一行一个 event record。课程里不需要数据库也能保留 run trail。未来如果真的要换成 database store，也应该保持同样的 append/read contract。

## Approval And Sandbox Policies

Approval policy 处理“这个 tool 能不能执行”：

```python
from research_core.production import ApprovalMode, ApprovalPolicy, ApprovalRule

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

for subject in ("retriever.search", "shell.exec", "email.send"):
    print(approval.decide(subject).to_record())
```

Sandbox policy 处理“这个路径或网络能不能碰”：

```python
from pathlib import Path

from research_core.production import SandboxPolicy

workspace = Path("tmp/course07-workspace")
sandbox = SandboxPolicy(
    readable_paths=(workspace,),
    writable_paths=(workspace / "outputs",),
    blocked_paths=(workspace / "secrets",),
    allow_network=False,
    max_runtime_seconds=15,
)

print(sandbox.decide_path(workspace / "notes.md", access="read").to_record())
print(sandbox.decide_path(workspace / "outputs/report.md", access="write").to_record())
print(sandbox.decide_path(workspace / "secrets/token.txt", access="read").to_record())
print(sandbox.network_decision().to_record())
```

重点不是“这就是完整安全系统”。重点是：安全判断要变成 typed decision record，而不是散落在 prompt、README 或 if statement 里的口头规则。

## Failure Lab Preview

故意把 sandbox access 写成不存在的动作：

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

这是一种好失败。contract 不会猜 `execute` 是什么意思，也不会偷偷当成 read 或 write。生产 readiness 的一部分，就是让坏输入在边界处清楚地失败。

## Eval Gate

运行：

```bash
uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
```

核心自查：

```python
diagnostics = RunDiagnostics.from_events(events)
assert diagnostics.event_count == 4
assert diagnostics.event_type_counts["error"] == 1
assert diagnostics.error_summaries[0]["message"] == "fixture missing"

gate_tmp = TemporaryDirectory()
gate_store = JsonlRunEventStore(Path(gate_tmp.name) / "events.jsonl")
gate_store.append_many(events)
assert [event.id for event in gate_store.read_run("run_7")] == [
    "evt_1",
    "evt_2",
    "evt_3",
    "evt_4",
]

assert approval.decide("retriever.search").mode is ApprovalMode.ALLOW
assert approval.decide("email.send").requires_review is True
assert sandbox.network_decision().allowed is False
```

## Checkpoint

继续下一章前，用自己的话回答：

1. 为什么 Phase 7 不从云日志、OAuth 或数据库开始？
2. `RunDiagnostics` 和 raw `RunEvent` trail 分别解决什么问题？
3. 为什么 JSONL store 要按 `run_id` 读回 events？
4. `ApprovalPolicy` 和 `SandboxPolicy` 的边界有什么不同？
5. 为什么 `access="execute"` 应该失败，而不是被自动解释成 read 或 write？

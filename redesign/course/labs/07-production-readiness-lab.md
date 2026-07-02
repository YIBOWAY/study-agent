# Lab 07: Production Readiness

这个 lab 让你把 Chapter 07 的本地 production-readiness contract 亲手跑一遍。你要证明四件事：

1. 一段 `RunEvent` trajectory 可以被 `RunDiagnostics` 摘成可读的事故摘要。
2. 同一段 event trail 可以被 `JsonlRunEventStore` 追加写入，再按 `run_id` 原顺序读回。
3. `ApprovalPolicy` 和 `SandboxPolicy` 能在执行前给出 allow、deny、require approval、blocked path、network disabled 等 typed decision。
4. 坏输入会在 contract 边界清楚失败，而不是悄悄制造不可信记录。

预计时间：60 到 80 分钟。全程离线、deterministic，不需要数据库、云服务、API key 或网络。

## Goal

| Tier | 你做什么 | 你要证明 |
| --- | --- | --- |
| L1 Follow | 跟着构造 `run_7` events，生成 diagnostics，写入 JSONL，再跑 approval/sandbox happy path | run 摘要可读、event replay 保序、policy decision 可检查 |
| L2 Modify/Break-Fix | 修改 trajectory 和 policy 规则，先预测再验证；逐个打破生产边界 | 诊断随 event 改变、approval first-match/default 清楚、坏输入被 contract 拒绝 |
| L3 Design | 不给 skeleton，为一个本地 report-export 场景设计 production-readiness policy | diagnostics 单 run、JSONL 保序、未知外部动作要 review/deny、secrets 被挡、network 显式 |

## Setup

所有命令默认从 `redesign/` 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

保持这个 shell 打开，后面 L1、L2 会复用变量。先确认 focused production tests 是绿的：

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
```

## L1 Follow: Summarize And Replay A Failed Run

目标：照着跑一遍，先不要改。你要看到两件事：diagnostics 能把失败 run 摘成可读记录；JSONL store 能按 `run_id` 读回原始 events。

### Step 1: Build the run_7 event trail

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
record = diagnostics.to_record()

print(record["run_id"])
print(record["event_count"])
print(record["event_type_counts"])
print(record["error_summaries"][0]["message"])
```

Expected output:

```text
run_7
4
{'model_request': 1, 'tool_call': 1, 'eval_result': 1, 'error': 1}
fixture missing
```

Self-check:

```python
assert diagnostics.run_id == "run_7"
assert diagnostics.event_count == 4
assert diagnostics.error_summaries[0]["kind"] == "tool_error"
assert diagnostics.error_summaries[0]["message"] == "fixture missing"
```

### Step 2: Write and replay the event trail

```python
tmp = TemporaryDirectory()
path = Path(tmp.name) / "runs" / "events.jsonl"

store = JsonlRunEventStore(path)
store.append_many(events)

print(path.exists())
print(store.list_run_ids())
print([event.id for event in store.read_run("run_7")])
print(store.read_run("missing"))
```

Expected output:

```text
True
('run_7',)
['evt_1', 'evt_2', 'evt_3', 'evt_4']
()
```

Self-check:

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

### Step 3: Read approval and sandbox decisions

```python
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

print("retriever:", allowed.mode.value, allowed.requires_review)
print("shell:", denied.mode.value, denied.requires_review)
print("email:", review.mode.value, review.requires_review)

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

print("read:", read_decision.allowed, read_decision.reason)
print("write:", write_decision.allowed, write_decision.reason)
print("secret:", secret_decision.allowed, secret_decision.reason)
print("network:", network_decision.allowed, network_decision.reason)
```

Expected output:

```text
retriever: allow False
shell: deny False
email: require_approval True
read: True path is allowed for read
write: True path is allowed for write
secret: False path is blocked by sandbox policy
network: False network access is disabled
```

Self-check:

```python
assert allowed.mode is ApprovalMode.ALLOW
assert denied.mode is ApprovalMode.DENY
assert review.requires_review is True
assert read_decision.allowed is True
assert write_decision.allowed is True
assert secret_decision.allowed is False
assert network_decision.allowed is False
```

### Exercise Feedback - L1 Follow

**Common Errors**:

1. `ModuleNotFoundError: No module named 'research_core'` - 你可能没有从 `redesign/` 运行，或漏了 `PYTHONPATH=packages/research_core/src`。
2. 直接打印 `diagnostics.event_type_counts` 看到 `mappingproxy(...)` - 这是不可变保护。面向输出时用 `diagnostics.to_record()["event_type_counts"]`。
3. 以为 `email.send` 被允许了 - 它没有匹配任何 rule，所以走 default `require_approval`。
4. 以为 secrets 在 workspace 里所以可读 - `blocked_paths` 优先于 readable/writable roots。

**Failure Output Interpretation**: 如果 `event_count` 不等于 4，先看你是不是漏了某个 event。 如果 `store.list_run_ids()` 为空，说明你还没 `append_many(events)`。 如果 `secret_decision.allowed` 是 True，检查 `blocked_paths` 是否写成了 `workspace / "secrets"`。

**Where To Go Back**: 回到 Chapter 07 的 Section 1「本地安全台的五个岗位」和 Section 2-4，确认 diagnostics、JSONL store、approval、sandbox 各守哪一道边界。

**Why Correct Answer Is Correct**: L1 证明 production readiness 的最小闭环：同一段 run 可以被摘要、保存、读回，并且执行边界能产出 typed decision。你还没有设计新 policy，但已经能解释什么被允许、什么被拒绝、什么需要人审。

## L2 Modify/Break-Fix: Change The Run, Tighten The Policy, Then Break The Boundaries

目标：先预测，再验证。L2 分三步：改 trajectory 看 diagnostics 怎样变化；改 approval/sandbox policy 看 decision 怎样变化；再逐个打破 production boundary，读错误信息并修正。

### Step 1: Add one event and predict the new diagnostics

预测：如果给 `run_7` 追加一个 `tool_result` event，`event_count` 会从 4 变成 5，`event_type_counts` 会多出 `tool_result: 1`，但 error summary 仍然指向 `fixture missing`。

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

print(modified_record["event_count"])
print(modified_record["event_type_counts"])
print(modified_record["error_summaries"][0]["message"])
```

Expected output:

```text
5
{'model_request': 1, 'tool_call': 1, 'tool_result': 1, 'eval_result': 1, 'error': 1}
fixture missing
```

Self-check:

```python
assert modified.event_count == 5
assert modified.to_record()["event_type_counts"]["tool_result"] == 1
assert modified.error_summaries[0]["message"] == "fixture missing"
```

### Step 2: Tighten approval and open network deliberately

预测：如果你给 `email.*` 加一条 deny rule，`email.send` 不再走 default review，而是明确 deny。与此同时，如果你显式打开 network sandbox，network decision 会从 disabled 变成 enabled。

```python
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
print(email_decision.mode.value, email_decision.reason, email_decision.matched_rule)

network_sandbox = SandboxPolicy(
    readable_paths=(workspace,),
    writable_paths=(workspace / "outputs",),
    blocked_paths=(workspace / "secrets",),
    allow_network=True,
    max_runtime_seconds=15,
)
open_network = network_sandbox.network_decision()
print(open_network.allowed, open_network.reason)
```

Expected output:

```text
deny Outbound email is blocked in the lab. email.*
True network access is enabled
```

Self-check:

```python
assert email_decision.mode is ApprovalMode.DENY
assert email_decision.matched_rule == "email.*"
assert open_network.allowed is True
```

### Step 3: Break/fix the production boundaries

每个 Break 都要先回答一个诊断问题：这道护栏在守什么？

**Break A - empty events**。诊断问题：没有 event，diagnostics 能知道 run_id 吗？

```python
try:
    RunDiagnostics.from_events(())
except ValueError as exc:
    print(exc)
```

Expected output:

```text
events must not be empty
```

Fix: 只对真实 event trail 生成 diagnostics。

**Break B - mixed run IDs**。诊断问题：把两个 run 混在一起，会制造什么假摘要？

```python
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
    print(exc)
```

Expected output:

```text
events must belong to one run_id
```

Fix: 先按 `run_id` 分组，再分别诊断。

**Break C - invalid JSONL schema**。诊断问题：只要文件是 JSON，就能当 event log 读吗？

```python
broken_tmp = TemporaryDirectory()
broken_path = Path(broken_tmp.name) / "events.jsonl"
broken_path.write_text('{"schema_version": "wrong", "event": {}}\n', encoding="utf-8")
broken_store = JsonlRunEventStore(broken_path)

try:
    broken_store.read_all()
except ValueError as exc:
    print(exc)
```

Expected output:

```text
unsupported event log schema at line 1
```

Fix: 用当前 store 写入，或者写迁移器后再读旧 schema。

**Break D - blank approval subject**。诊断问题：空 subject 能被审计或匹配 rule 吗？

```python
try:
    approval.decide(" ")
except ValueError as exc:
    print(exc)
```

Expected output:

```text
subject must not be empty
```

Fix: 调 policy 前给出真实 tool subject，比如 `retriever.search`。

**Break E - invalid sandbox access**。诊断问题：如果把 `execute` 偷偷当成 read 或 write，会隐藏什么风险？

```python
try:
    sandbox.decide_path(workspace / "script.sh", access="execute")
except ValueError as exc:
    print(type(exc).__name__, str(exc))
else:
    raise AssertionError("Expected invalid access to fail")
```

Expected output:

```text
ValueError access must be one of: read, write
```

Fix: 新动作要有新 contract 和新测试，不能临时解释。

**Break F - blocked path and disabled network are denied decisions**。诊断问题：这两个不是 exception，为什么仍然是生产边界？

```python
print(secret_decision.allowed, secret_decision.reason)
print(network_decision.allowed, network_decision.reason)
```

Expected output:

```text
False path is blocked by sandbox policy
False network access is disabled
```

Fix: 不要绕过 policy；如果任务真的需要 secrets 或 network，必须重新设计 policy 和人工审批。

### Exercise Feedback - L2 Modify/Break-Fix

**Common Errors**:

1. 修改 event 后忘了同一个 `run_id` - 这会触发 mixed run_id，而不是正常 diagnostics。
2. 以为 `email.*` deny rule 会影响 `retriever.search` - approval 是 first match；不同 subject 匹配不同 rule。
3. 把 `allow_network=True` 当成真实网络调用 - 这里只是 decision record，不会发起网络请求。
4. 把 blocked path/network disabled 当成异常 - 它们是 `SandboxDecision`，用 `allowed=False` 表示拒绝。
5. Break 块裸调用不捕获异常 - markdown gate 会中断整份 lab；每个异常型 Break 必须 `try/except`。

**Failure Output Interpretation**: `events must not be empty` 指向没有输入；`events must belong to one run_id` 指向混合 run；`unsupported event log schema` 指向持久化格式不可信；`subject must not be empty` 指向无法审计的 tool subject；`access must be one of` 指向 sandbox action 不受支持。

**Where To Go Back**: 回到 Chapter 07 的 Section 5「打破 production 边界」，逐条对照每个错误守住的 boundary。再回到 Section 4 看 approval 和 sandbox 的职责差异。

**Why Correct Answer Is Correct**: L2 证明 production readiness 不是一组静态说明，而是一组随输入变化的 contract：trajectory 变了，diagnostics 变；policy 变了，decision 变；坏输入出现时，边界清楚拒绝。

## L3 Design: Design A Production-Readiness Boundary For Report Export

目标：不给 skeleton，你自己为一个**本地 report-export 场景**设计 production-readiness policy。

场景：Capstone 里的助手准备把最终论文报告导出到 `tmp/report-export/outputs/final.md`。它需要读取 `tmp/report-export/notes/` 下的草稿，写入 `tmp/report-export/outputs/`，但绝不能读取 `tmp/report-export/secrets/`。它允许 `retriever.*`，`report.export` 需要人工审批，`shell.*` 必须 deny。网络默认关闭。

你要做的：

- 设计一个新的 event tuple，代表一次 report export run。它必须只属于一个 `run_id`，并至少包含 `model_request`、`tool_call`、`tool_result`、`eval_result`。
- 用 `RunDiagnostics.from_events(...)` 证明 diagnostics 是单 run，且 event count 正确。
- 用 `JsonlRunEventStore` 追加写入并按 `run_id` 读回，证明 event 顺序不变。
- 设计 `ApprovalPolicy`，让 `retriever.*` allow，`report.export` require approval，`shell.*` deny。
- 设计 `SandboxPolicy`，让 notes 可读、outputs 可写、secrets blocked、network disabled。
- 写出断言证明这些 invariants 成立。

下面是最低自查模板。注意：这段引用你自己发明的 L3 变量（`l3_events` / `l3_diagnostics` / `l3_store` / `l3_approval` / `l3_sandbox` / `l3_workspace`），所以它是**设计验收模板，不是直接粘贴运行的完整示例**；可运行参考答案在 solution 里。

```text
# 1. diagnostics 只接受单个 run_id，且数量正确
assert len({event.run_id for event in l3_events}) == 1
assert l3_diagnostics.event_count == len(l3_events)

# 2. JSONL replay 保序
assert [event.id for event in l3_store.read_run("run_export")] == [
    event.id for event in l3_events
]

# 3. approval rules 命中预期
assert l3_approval.decide("retriever.search").mode is ApprovalMode.ALLOW
assert l3_approval.decide("report.export").requires_review is True
assert l3_approval.decide("shell.exec").mode is ApprovalMode.DENY

# 4. sandbox rules 命中预期
assert l3_sandbox.decide_path(l3_workspace / "notes/draft.md", access="read").allowed is True
assert l3_sandbox.decide_path(l3_workspace / "outputs/final.md", access="write").allowed is True
assert l3_sandbox.decide_path(l3_workspace / "secrets/token.txt", access="read").allowed is False
assert l3_sandbox.network_decision().allowed is False
```

### Exercise Feedback - L3 Design

**Common Errors**:

1. 在 L3 events 里混入两个 `run_id` - diagnostics 必须拒绝这种假 run。
2. 只写 diagnostics，不写 JSONL replay - production readiness 既要摘要，也要可读回原始 event trail。
3. 把 `report.export` 直接 allow - 在这个场景里导出报告是对外产物，应先 require approval。
4. 忘了把 secrets 目录放进 `blocked_paths` - 它即使在 workspace 内，也必须被显式挡住。
5. 以为 L3 有唯一答案 - 它考的是 invariants：单 run、replay 保序、审批默认安全、secrets blocked、network 显式。

**Failure Output Interpretation**: 如果 diagnostics 报 mixed run ID，先检查每个 `RunEvent.run_id`。如果 replay 顺序断言失败，检查 append 顺序。 如果 `report.export` 没有 require review，检查 rule 顺序和 default mode。 如果 secrets 变成 allowed，检查 `blocked_paths` 是否比 readable/writable roots 更具体。

**Where To Go Back**: 回到 Chapter 07 的 Section 1「本地安全台的五个岗位」和 Section 6「产品连接与 Eval Gate」，把 L3 当成 R8 Capstone 前的一次 readiness rehearsal。

**Why Correct Answer Is Correct**: L3 不考一个固定答案，而考生产边界的不变量。只要你的设计能保存、读回、审计、审批、阻断 secrets/network，并用断言证明这些事，它就是一份可辩护的 readiness boundary。

## Reflection

做完 lab 后，用自己的话回答：

1. `RunDiagnostics` 为什么要拒绝空 event list 或混合 run_id？
2. `JsonlRunEventStore` 的 append/read contract 和数据库有什么不同？它现在够用，是因为课程还没有哪些真实生产要求？
3. 为什么 `email.send` 默认是 `require_approval`，而 L3 的 `report.export` 也应该 require approval？
4. blocked path 和 disabled network 都不是 exception，为什么它们仍然是 production boundary？
5. **Tradeoff**：如果未来要支持 `execute` 或真实网络访问，你会新增什么 contract、测试和人工审批，而不是在现有 policy 里偷偷放行？

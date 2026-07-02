# Part 7: Production Readiness - 先让本地助手可复盘、可审计、能挡住危险动作

> 接 Part 6。你已经能让本地论文研究助手运行、引用证据、写记忆、委派子任务、展示 Workbench，还能解释为什么暂时保持手写 runtime。Part 7 换一个上线前最现实的问题：如果这个助手交给别人用，出事以后你能不能复盘？记录能不能保存？危险动作能不能在执行前被挡住？文档索引能不能信？

预计时间：70 到 95 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要认得 Part 1 的 `RunEvent` event trail、Part 5 的 Workbench 记录边界，以及 Part 6 的 "先离线复现，再谈引入外部系统" 思路。
- **Before you start**: 先完成 Part 1 的 Agent Kernel、Part 5 的 Workbench Product、Part 6 的 Framework Comparisons。
- **You will build**: 一层完全离线的 production-readiness contract：用 `RunDiagnostics` 总结 run，用 `JsonlRunEventStore` 保存和读回 event trail，用 `ApprovalPolicy` 判断 tool subject，用 `SandboxPolicy` 判断本地路径和网络边界。
- **You will be able to explain**: 为什么 production readiness 不是先上云；diagnostics 和 raw events 分别解决什么问题；JSONL replay 为什么足够做课程里的本地审计；approval 和 sandbox 的边界有什么不同；为什么坏输入要在 contract 边界清楚失败。
- **You will prove it works by running**: `PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q`。
- **Offline guarantee**: 全程 deterministic 本地对象；没有真实云日志、数据库、OAuth、队列、provider SDK、网络调用或部署自动化。

## 你的本地论文研究助手快要交给别人用了

前六个 Part 之后，这个助手已经不像 demo 了。它有 event trail，有 evidence chain，有 memory，有 delegation，有工作台，也有一套解释 "为什么不直接换框架" 的比较方法。

这时如果研究员说：

> "我想让团队里的其他人也用它。万一它写错、漏掉证据、碰到不该碰的文件，或者文档链接断了，我们能查清楚吗？"

这就是 production readiness 的第一层。不是先上 Kubernetes，不是先接 OAuth，不是先买数据库，而是先回答四个朴素问题：

1. **What happened?** 出事后能不能快速看懂刚才发生了什么？
2. **What survives?** event trail 能不能保存下来、按 run_id 读回？
3. **What is allowed?** tool、文件、网络边界能不能在执行前给出 typed decision？
4. **Can we trust the map?** 文档和课程索引能不能指向真实存在的文件？

> [BIG] **大局观**：Part 7 不把项目变成云平台。它先把 "可复盘、可审计、可拦截" 变成本地可测试 contract。等以后真的接日志系统、数据库或审批 UI，这些外部系统只是包住这些 contract，而不是替代它们。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [x] Part 2: Research Core, evidence chain
  [x] Part 3: Memory and Skills
  [x] Part 4: Delegation
  [x] Part 5: Workbench Product
  [x] Part 6: Framework Comparisons
  [*] Part 7: Production Readiness
      [*] RunDiagnostics: what happened
      [*] JsonlRunEventStore: what survives
      [*] ApprovalPolicy: which tool subject needs allow/deny/review
      [*] SandboxPolicy: which path/network action is allowed
      [*] docs freshness: whether the project map can be trusted
  [ ] Capstone: complete offline paper research assistant
```

## Section 1 [LIGHT Concept]: 本地安全台的五个岗位

把 production readiness 想成一个**本地安全台**。安全台不替助手做研究，它只负责让每次 run 有复盘材料、保存记录和执行边界。

| Contract | Plain-language role | What to inspect |
| --- | --- | --- |
| `RunDiagnostics` | 事故摘要员：把一串 `RunEvent` 摘成数量、类型和错误摘要 | `diagnostics.to_record()` |
| `JsonlRunEventStore` | 黑匣子：一行一个 event，追加写入，再按 `run_id` 读回 | `store.list_run_ids()`, `store.read_run(...)` |
| `ApprovalPolicy` | 人类审批门：某个 tool subject 是 allow、deny，还是 require approval | `approval.decide(subject).to_record()` |
| `SandboxPolicy` | 本地围栏：某个 path/network action 是否允许 | `sandbox.decide_path(...)`, `sandbox.network_decision()` |
| docs freshness | 地图检查员：索引里的路径是否真的存在 | `tests/course/test_docs_freshness.py` |

> [DD] **设计决策**：这些 contract 都在本地、离线、可测试的 Python 对象里。不要把 production readiness 一开始就交给云日志、数据库或网页审批流。外部基础设施可以晚点接，但它应该包住这些 contract，而不是把边界规则藏到平台配置里。

### 复盘链路：从 event trail 到可审计记录

```text
RunEvent trajectory
      |
      v
RunDiagnostics.from_events(...)
      |
      +--> event_count / event_type_counts / error_summaries
      |
      v
JsonlRunEventStore.append_many(events)
      |
      +--> events.jsonl (one event record per line)
      |
      v
read_run(run_id) -> replay / audit / Workbench evidence
```

### 执行边界：先问 policy，再执行动作

```text
tool subject                 local path / network
     |                               |
     v                               v
ApprovalPolicy.decide(...)    SandboxPolicy.decide_path(...)
     |                               |
     +-----------+-------------------+
                 v
         typed decision record
         allow / deny / require_approval
```

> [CHECK] **检查一下**：`ApprovalPolicy` 管的是 "这个 tool subject 能不能执行或需要人审"，`SandboxPolicy` 管的是 "这个本地路径或网络动作能不能碰"。一个是工具审批，一个是执行环境围栏，不要混成一个万能 if statement。

## Section 2 [FULL Build]: 造一段失败 run，然后生成 diagnostics

这一章所有 Python snippet 都从 `redesign/` 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

先准备 imports 和一段四个 event 的 run。它模拟一次 RAG 评测：模型规划、调用检索工具、工具失败、eval 记录 citation 缺失。

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

print("events ready:", len(events))
```

Expected output:

```text
events ready: 4
```

### Build: 生成事故摘要

```python
diagnostics = RunDiagnostics.from_events(events)
record = diagnostics.to_record()

print("run_id:", record["run_id"])
print("event_count:", record["event_count"])
print("event_type_counts:", record["event_type_counts"])
print("first_error:", record["error_summaries"][0])
```

Expected output:

```text
run_id: run_7
event_count: 4
event_type_counts: {'model_request': 1, 'tool_call': 1, 'eval_result': 1, 'error': 1}
first_error: {'event_id': 'evt_3', 'step': 'retrieve', 'kind': 'tool_error', 'message': 'fixture missing'}
```

这不是 dashboard。它是最小事故摘要：run 有多少 event，哪些类型出现过，错误在哪个 event 里。raw event trail 还在，但你不需要每次先肉眼翻四个 payload。

> [TRAP] **常见误解**：`RunDiagnostics` 不是替代 event trail。它是 event trail 的目录和摘要。真正要做审计时，仍然要能读回原始 events。

## Section 3 [FULL Inspect]: 把 event trail 写进 JSONL，再按 run_id 读回

`JsonlRunEventStore` 做一件很窄的事：追加写 event log。课程先用 JSONL，不是因为 JSONL 比数据库高级，而是因为它足够透明：一行一个 record，打开就能看，测试也容易。

```python
tmp = TemporaryDirectory()
path = Path(tmp.name) / "runs" / "events.jsonl"

store = JsonlRunEventStore(path)
store.append_many(events)

print("path exists:", path.exists())
print("run_ids:", store.list_run_ids())
print("replayed_ids:", [event.id for event in store.read_run("run_7")])
print("missing:", store.read_run("missing"))
```

Expected output:

```text
path exists: True
run_ids: ('run_7',)
replayed_ids: ['evt_1', 'evt_2', 'evt_3', 'evt_4']
missing: ()
```

这段输出证明三件事：

- store 会创建父目录；
- 读回顺序就是 append 顺序；
- 不存在的 run 不会伪造数据，只返回空 tuple。

> [DEEP] **为什么 JSONL 够用**：本课程还没到真实数据库、迁移、锁、并发写入和权限模型。现在先把 append/read contract 钉牢，未来换 database store 时，只要保持同样的语义，课程里的复盘逻辑就不会变。

## Section 4 [FULL Build]: 写 approval 和 sandbox 边界

先写 tool approval policy。它的规则是 first match wins：先匹配到哪条 rule，就用哪条；都没匹配到，就走 default。

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

for subject in ("retriever.search", "shell.exec", "email.send"):
    decision = approval.decide(subject)
    print(subject, decision.mode.value, decision.requires_review, decision.matched_rule)
```

Expected output:

```text
retriever.search allow False retriever.*
shell.exec deny False shell.*
email.send require_approval True 
```

`email.send` 没有被 allow，也没有被 deny；它落到 default `require_approval`。这就是一个很常见的生产边界：未知动作不该默默放行，但也不一定永远禁止，先让人审。

再写 sandbox policy。它不看 tool 名字，它只回答本地路径和网络边界。

```python
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
outside_decision = sandbox.decide_path(Path("tmp/outside.txt"), access="read")
network_decision = sandbox.network_decision()

print("read:", read_decision.allowed, read_decision.reason)
print("write:", write_decision.allowed, write_decision.reason)
print("secret:", secret_decision.allowed, secret_decision.reason)
print("outside:", outside_decision.allowed, outside_decision.reason)
print("network:", network_decision.allowed, network_decision.reason)
```

Expected output:

```text
read: True path is allowed for read
write: True path is allowed for write
secret: False path is blocked by sandbox policy
outside: False path is not allowed for read
network: False network access is disabled
```

`blocked_paths` 优先于 readable/writable roots。`tmp/course07-workspace/secrets/token.txt` 在 workspace 里面，但仍然被挡住，因为 secrets 子目录显式 blocked。

> [CHECK] **检查一下**：deny/review/blocked 都不是 "程序坏了"。它们是 typed decision record，说明 contract 在执行前做出了判断。真正危险的是没有 record，只靠 prompt 说 "请不要访问秘密文件"。

## Section 5 [BREAK/FIX]: 打破 production 边界

下面每个 Break 都自己捕获错误。Production readiness 的重点不是永远不失败，而是**在正确的边界、用清楚的信息失败**。

### Break 1: 空 event list 没法诊断

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

Diagnosis: 没有 event，就没有 run_id、数量或错误摘要。Fix: 只对真实 event trail 生成 diagnostics。

### Break 2: 混合 run_id 不能当成一次 run

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

Diagnosis: 把两个 run 混在一起会制造假摘要。Fix: 先按 `run_id` 分组，再分别诊断。

### Break 3: JSONL schema 不对就拒绝读

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

Diagnosis: persistence contract 不是 "只要像 JSON 就读"。schema version 不对，读出来的 event 语义就不能信。Fix: 用当前 `JsonlRunEventStore` 写入，或者写迁移器再读旧 schema。

### Break 4: approval subject 不能为空

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

Diagnosis: 空 subject 没法匹配 rule，也没法审计。Fix: 调 policy 前必须给出真实 tool subject，比如 `retriever.search`。

### Break 5: sandbox access 只认 read/write

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

Diagnosis: `execute` 不是这个课程 contract 支持的动作。Fix: 不要偷偷把 execute 当成 read 或 write；如果未来真的要支持执行脚本，那是一个新 contract 和新测试。

### Break 6: blocked path 和 network disabled 是拒绝型 decision

```python
print(secret_decision.allowed, secret_decision.reason)
print(network_decision.allowed, network_decision.reason)
```

Expected output:

```text
False path is blocked by sandbox policy
False network access is disabled
```

Diagnosis: 这两个不是 Python exception，而是明确的 deny record。Fix: 不要绕过 policy；如果某个任务真的需要 secrets 或 network，就要在新 phase 里重新设计 policy、测试和人工审批，而不是在代码里临时放行。

> [DEEP] **为什么这些失败是好事**：它们都在进入生产边界时失败，而不是等到报告写完、文件泄露、日志坏掉以后才发现。Production readiness 的第一层，就是让坏输入在边界处留下清楚、可测试、可解释的失败。

## Section 6 [FULL Boundary]: 产品连接与 Eval Gate

Part 7 往前接住前六个 Part：

```text
Part 1 RunEvent trail
      |
      v
Part 7 RunDiagnostics + JsonlRunEventStore
      |
      v
Part 5 Workbench can show/audit saved records

Part 2 evidence/report, Part 3 memory, Part 4 delegation, Part 6 framework record
      |
      v
Capstone must ship with event log + diagnostics + policy decisions
```

Part 7 也给 R8 Capstone 定了底线：最终项目不能只交一个漂亮 report。它还要能交出 event log、diagnostics summary、approval/sandbox decisions 和 readiness checklist，否则报告出了问题没人能复盘。

> [DD] **设计决策**：Part 7 的 production-readiness contract 仍然不 import FastAPI、React、数据库或云 SDK。Workbench 可以展示这些 records，API 可以 transport 它们，但 contract 本身要能在纯 Python 测试里跑通。

### Eval Gate

从 `redesign/` 运行：

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/research_core/test_production_observability.py tests/research_core/test_production_persistence.py tests/research_core/test_production_policy.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
cd apps/web && npm ci && npm run build
```

核心自查（沿用本章同一个 Python session 的变量；若另开 shell，先重跑 Section 2-4）：

```python
assert diagnostics.run_id == "run_7"
assert diagnostics.event_count == 4
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
assert secret_decision.allowed is False
assert network_decision.allowed is False

print("production readiness self-check passed")
```

Expected output:

```text
production readiness self-check passed
```

## Reflection

继续 Capstone 前，用自己的话回答：

1. 为什么 Part 7 不从云日志、OAuth、数据库或部署脚本开始？
2. `RunDiagnostics` 和 raw `RunEvent` trail 分别解决什么问题？为什么 diagnostics 不能替代 raw events？
3. JSONL store 为什么按 `run_id` 读回 events？如果混合 run_id，会制造什么假象？
4. `ApprovalPolicy` 和 `SandboxPolicy` 的边界有什么不同？为什么不能只靠一个 prompt 说 "不要做危险事"？
5. **Tradeoff**：JSONL 在课程里够用，但真实生产里可能不够。什么时候你会引入数据库或云日志？引入以后，哪些 contract 语义必须保持不变？

# Solution 05: Workbench Product

这份 solution 用来校准理解。请先自己完成 Lab 05，再看这里。尤其是 L3：这里给的是一个参考设计，不是唯一正确答案。

这个 lab 既有只用 core 的块，也有要 import `research_api` 的 API 块，所以统一用**同时带 api 和 core** 的 path 打开一个 Python shell（它是 core-only path 的超集）：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run python
```

也可以先确认 focused tests 是绿的：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
```

## Imports

一次把三层用到的名字都 import 好：core 的产品契约、`from_*` adapter 依赖的原始 domain 对象、以及 FastAPI transport。

```python
from fastapi.testclient import TestClient
from research_api.main import create_app
from research_core.memory import MemoryKind, MemoryRecord
from research_core.product import (
    WorkbenchDelegationNode,
    WorkbenchEvalItem,
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReport,
    WorkbenchRun,
    WorkbenchSkillItem,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
    build_demo_workbench_snapshot,
)
from research_core.research import (
    Claim,
    ClaimSourceLink,
    Evidence,
    Report,
    ResearchRunStatus,
    Source,
    build_claim_source_links,
)
from research_core.runtime import RunEvent, RunEventType
```

## L1 Follow Solution

先 inspect 别人拼好的成品快照，再用 `TestClient` 离线打三个 endpoint，证明 core 层 `to_record()` 的九面板和 FastAPI transport 搬出来的九面板是**同一个形状**。

```python
demo = build_demo_workbench_snapshot()
record = demo.to_record()

assert sorted(record.keys()) == [
    "delegation",
    "evals",
    "memory",
    "project",
    "report",
    "run",
    "skills",
    "sources",
    "timeline",
]
assert [item["type"] for item in record["timeline"]] == [
    "model_request",
    "tool_call",
    "delegate_start",
    "delegate_finish",
]
assert record["run"]["status"] == "completed"
assert record["delegation"][0]["role"] == "evidence-reviewer"
assert record["memory"][0]["summary_row"]["tags"] == ["citation", "reporting"]
```

```python
client = TestClient(create_app())

health = client.get("/health")
snapshot_response = client.get("/api/workbench/snapshot")
timeline_response = client.get("/api/workbench/timeline")

assert health.status_code == 200
assert health.json() == {
    "status": "ok",
    "service": "research-workbench-api",
}
assert snapshot_response.status_code == 200
assert timeline_response.status_code == 200
assert sorted(snapshot_response.json().keys()) == sorted(record.keys())
assert timeline_response.json() == snapshot_response.json()["timeline"]
```

What This Proves:

- `WorkbenchSnapshot.to_record()` 是产品层的最小契约：九个面板 key 一次定死，一个不少。
- timeline 忠实保留了 runtime event 的顺序，delegation 信息在产品层已经可见。
- FastAPI 只是 transport：`/api/workbench/snapshot` 的九个 key 和 core 层逐字一致，`/api/workbench/timeline` 就是同一 record 的 `timeline` 切片。

Why This Design:

- API 和 UI 消费的是**形状契约**，不是某一份具体数据；只要 record 稳定，transport 就不需要发明第二套形状。
- 用 `sorted(...keys())` 逐字对齐 core 和 API，是证明 "transport 没偷偷改契约" 的最直接方式，比对比某个字段值更可靠。
- `TestClient` 离线跑，不起真实服务器、不联网，让产品契约在没有 provider 凭证时也能被课程和 CI 验证。

## L2 Modify / Break-Fix Solution

L2 分两条线：先证明返回的 record 是独立拷贝（copy 安全），再故意改坏原始对象，看契约在**构造时**怎么挡住五种自相矛盾的快照。

### Copy safety

改坏 API 返回的 record 里的深层字段，重新 `GET` 一次，第二次拿到的仍是原值——因为 `to_record()` 每次返回独立拷贝。

```python
data = snapshot_response.json()
data["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
data["sources"][0]["evidence"][0]["claim_ids"].append("mutated")
data["memory"][0]["summary_row"]["tags"].append("mutated")

fresh = client.get("/api/workbench/snapshot").json()

assert fresh["timeline"][0]["metadata"]["tokens"]["prompt"] == 128
assert fresh["sources"][0]["evidence"][0]["claim_ids"] == ["claim_1"]
assert fresh["memory"][0]["summary_row"]["tags"] == ["citation", "reporting"]
```

### Assemble a valid snapshot from raw objects

Break/Fix 之前，先用 `from_*` adapter 从原始 domain 对象拼一个**合法**的临床试验评审快照，作为后面打破的基准。引用链用 `build_claim_source_links(...)` 从同一批 evidence/sources 生成。

```python
l2_project = WorkbenchProject(id="project_trials", title="Clinical Trial Evidence Review")
l2_run = WorkbenchRun(
    id="run_trials",
    project_id="project_trials",
    title="Screen trial claims",
    question="Do the cited trials support the drug efficacy claim?",
    status=ResearchRunStatus.COMPLETED,
)

l2_source = Source(
    id="source_trial_a",
    uri="memory://trials/a",
    title="Trial A Report",
    content="Trial A reports a statistically significant efficacy improvement.",
)
l2_evidence = Evidence(
    id="evidence_efficacy",
    source_id="source_trial_a",
    quote="Trial A reports a statistically significant efficacy improvement.",
    location="table-2",
)
l2_claim = Claim(
    id="claim_efficacy",
    text="Trial A shows a significant efficacy improvement.",
    evidence_ids=["evidence_efficacy"],
)
l2_report = Report(
    id="report_trials",
    run_id="run_trials",
    title="Trial Evidence Findings",
    summary="Trial A supports the efficacy claim with a table-2 result.",
    claims=[l2_claim],
)
l2_links = build_claim_source_links(l2_report, evidence=[l2_evidence], sources=[l2_source])

l2_source_item = WorkbenchSourceItem.from_source(
    l2_source,
    summary="Primary efficacy trial.",
    evidence=[l2_evidence],
    claim_ids_by_evidence_id={"evidence_efficacy": ("claim_efficacy",)},
)
l2_report_item = WorkbenchReport.from_report(l2_report, claim_source_links=l2_links)
l2_timeline_item = WorkbenchTimelineItem.from_event(
    RunEvent(
        id="evt_request",
        run_id="run_trials",
        type=RunEventType.MODEL_REQUEST,
        payload={"tokens": {"prompt": 64}},
    ),
    title="Model request",
)

l2_snapshot = WorkbenchSnapshot(
    project=l2_project,
    run=l2_run,
    timeline=[l2_timeline_item],
    sources=[l2_source_item],
    report=l2_report_item,
)

assert sorted(l2_snapshot.to_record().keys()) == sorted(record.keys())
assert l2_snapshot.to_record()["report"]["claim_source_links"][0]["evidence_id"] == "evidence_efficacy"
```

### Break each of the five checks

只改**一个**原始对象——给 timeline 事件一个和 run 对不上的 `run_id`，其它照旧。`from_event` 只忠实翻译坏 `run_id`，守边界的是 `WorkbenchSnapshot` 的跨引用校验。每个 Break 块自己捕获异常并断言报错文本。

```python
bad_timeline_item = WorkbenchTimelineItem.from_event(
    RunEvent(
        id="evt_request",
        run_id="run_OTHER",
        type=RunEventType.MODEL_REQUEST,
        payload={"tokens": {"prompt": 64}},
    ),
    title="Model request",
)
try:
    WorkbenchSnapshot(
        project=l2_project,
        run=l2_run,
        timeline=[bad_timeline_item],
        sources=[l2_source_item],
        report=l2_report_item,
    )
except ValueError as exc:
    l2_timeline_error = str(exc)
else:
    raise AssertionError("Expected timeline run_id mismatch to fail")

assert l2_timeline_error == "timeline run_id must match run id"
```

**Break A — run 的 project_id 对不上 project**（project ↔ run 边界）。

```python
try:
    WorkbenchSnapshot(
        project=l2_project,
        run=WorkbenchRun(
            id="run_trials",
            project_id="project_WRONG",
            title="Screen trial claims",
            question="q",
        ),
    )
except ValueError as exc:
    l2_project_error = str(exc)
else:
    raise AssertionError("Expected run project_id mismatch to fail")

assert l2_project_error == "run project_id must match project id"
```

**Break B — report 引用了快照里不存在的 evidence**（report ↔ sources 证据链边界）。

```python
dangling_link = ClaimSourceLink(
    claim_id="claim_efficacy",
    claim_text="Trial A shows a significant efficacy improvement.",
    evidence_id="evidence_MISSING",
    source_id="source_trial_a",
    source_title="Trial A Report",
    source_uri="memory://trials/a",
    quote="q",
)
try:
    WorkbenchSnapshot(
        project=l2_project,
        run=l2_run,
        report=WorkbenchReport(
            id="report_trials",
            run_id="run_trials",
            title="Trial Evidence Findings",
            summary="s",
            claim_source_links=[dangling_link],
        ),
    )
except ValueError as exc:
    l2_report_error = str(exc)
else:
    raise AssertionError("Expected dangling evidence_id to fail")

assert l2_report_error == "report claim_source_links evidence_id must reference snapshot evidence"
```

**Break C — delegation node id 重复**（delegation 身份边界）。

```python
node_a = WorkbenchDelegationNode(
    id="task_dup",
    title="A",
    role="reviewer",
    status="completed",
    run_id="run_child_a",
)
node_b = WorkbenchDelegationNode(
    id="task_dup",
    title="B",
    role="reviewer",
    status="completed",
    run_id="run_child_b",
)
try:
    WorkbenchSnapshot(project=l2_project, run=l2_run, delegation=[node_a, node_b])
except ValueError as exc:
    l2_delegation_error = str(exc)
else:
    raise AssertionError("Expected duplicate delegation ids to fail")

assert l2_delegation_error == "delegation node ids must be unique"
```

**Break D — eval score 越界**（单个面板项数值域边界；比快照更早一层失败）。

```python
try:
    WorkbenchEvalItem(
        id="eval_bad",
        title="Bad eval",
        metric="efficacy",
        status="passed",
        score=1.5,
    )
except ValueError as exc:
    l2_eval_error = str(exc)
else:
    raise AssertionError("Expected out-of-range eval score to fail")

assert l2_eval_error == "score must be a number between 0 and 1"
```

What This Proves:

- `to_record()` 每次返回独立拷贝：改返回值污染不到 core snapshot，所以产品层可以放心让 UI 编辑、排序、过滤。
- 五种自相矛盾的快照都在**构造时**被拒绝——四条是快照跨引用校验（project↔run、run↔timeline、report↔sources、delegation 身份），一条是面板项自身的数值域校验（eval score）。
- 矛盾快照根本构造不出来，所以 UI 永远不需要处理"半坏的数据"。

Why This Design:

- eval score 越界比 `_validate_snapshot_references` 更早一层失败，因为如果 score 能是 1.5，前端的百分比、进度条、颜色和 eval gate 都会开始撒谎。
- referential integrity 放在 Python 契约里而不是 React 里：core 是唯一的真相源，任何 transport 或 UI 都拿不到一个自相矛盾的快照。
- Break 用 `from_event` 翻译坏 `run_id`、而不是手搓一个"修好的" `WorkbenchTimelineItem`，是因为正确做法是让原始 domain 对象就对，而不是发明第二套数据模型去绕过校验。

## L3 Design Solution

这是一个合法的参考设计，不是唯一正确答案。任何满足相同不变量的答案都可以：

- 九面板齐（`to_record()` 出九个 key），
- 跨引用全部合法（run↔project、timeline↔run、report 的 `evidence_id` 落在快照 sources 里），
- `to_record()` 返回独立拷贝，
- `summary_row()` 只投影列表需要的几列。

场景换成一个和前面完全不同的题目：**LLM 安全红队评审**——研究员想知道"某个越狱提示是否真的绕过了模型的安全护栏"。全程只用现有的 `from_*` adapter 和产品契约，不手搓面板项绕过 `from_*`。

```python
l3_project = WorkbenchProject(
    id="project_redteam",
    title="LLM Safety Red-Team Review",
)
l3_run = WorkbenchRun(
    id="run_redteam",
    project_id="project_redteam",
    title="Assess a jailbreak prompt",
    question="Does the jailbreak prompt actually bypass the safety guardrail?",
    status=ResearchRunStatus.COMPLETED,
)

l3_source = Source(
    id="source_jailbreak_log",
    uri="memory://redteam/jailbreak-log",
    title="Red-Team Transcript",
    content="The model refused the direct request but complied after a role-play framing.",
)
l3_evidence = Evidence(
    id="evidence_bypass",
    source_id="source_jailbreak_log",
    quote="The model complied after a role-play framing.",
    location="turn-4",
)
l3_claim = Claim(
    id="claim_bypass",
    text="The role-play framing bypasses the refusal guardrail.",
    evidence_ids=["evidence_bypass"],
)
l3_report = Report(
    id="report_redteam",
    run_id="run_redteam",
    title="Jailbreak Findings",
    summary="The role-play framing reliably bypasses the direct-request refusal.",
    claims=[l3_claim],
)
l3_links = build_claim_source_links(l3_report, evidence=[l3_evidence], sources=[l3_source])

l3_timeline_item = WorkbenchTimelineItem.from_event(
    RunEvent(
        id="evt_redteam_request",
        run_id="run_redteam",
        type=RunEventType.MODEL_REQUEST,
        payload={"tokens": {"prompt": 96}},
    ),
    title="Model request",
    summary="Replayed the jailbreak prompt against the guarded model.",
)
l3_source_item = WorkbenchSourceItem.from_source(
    l3_source,
    summary="Transcript proving the bypass.",
    evidence=[l3_evidence],
    claim_ids_by_evidence_id={"evidence_bypass": ("claim_bypass",)},
)
l3_report_item = WorkbenchReport.from_report(l3_report, claim_source_links=l3_links)
l3_memory = WorkbenchMemoryItem.from_memory_record(
    MemoryRecord(
        id="mem_refusal_rule",
        kind=MemoryKind.PINNED,
        content="Role-play framings must be re-tested after every guardrail change.",
        tags=["safety", "red-team"],
        importance=0.9,
    ),
    title="Refusal rule",
    summary="Pinned rule that keeps red-team findings actionable.",
)
l3_skill = WorkbenchSkillItem(
    id="skill_jailbreak_probe",
    title="Jailbreak probe",
    name="jailbreak-probe",
    description="Replays known jailbreak framings against a guarded model.",
    status="loaded",
    resources=("references/jailbreak-catalog.md", "scripts/probe.py"),
)
l3_eval = WorkbenchEvalItem(
    id="eval_refusal_rate",
    title="Refusal rate",
    metric="guardrail_refusal_rate",
    status="failed",
    score=0.4,
    details="The guardrail refused only 40% of the role-play framings.",
)
l3_delegation = WorkbenchDelegationNode(
    id="task_transcript_review",
    title="Transcript review",
    role="safety-reviewer",
    status="completed",
    run_id="run_child_transcript_review",
    summary="Confirmed the bypass turn is quoted with a source-backed link.",
)

l3_snapshot = WorkbenchSnapshot(
    project=l3_project,
    run=l3_run,
    timeline=[l3_timeline_item],
    delegation=[l3_delegation],
    sources=[l3_source_item],
    report=l3_report_item,
    memory=[l3_memory],
    skills=[l3_skill],
    evals=[l3_eval],
)
l3_record = l3_snapshot.to_record()
```

用四条不变量验收这个从零拼出来的快照：

```python
# 1. 九面板齐
assert sorted(l3_record.keys()) == [
    "delegation",
    "evals",
    "memory",
    "project",
    "report",
    "run",
    "skills",
    "sources",
    "timeline",
]

# 2. 跨引用合法：能 to_record() 说明构造时校验已过，再显式验三条关键边界
assert l3_record["run"]["project_id"] == l3_record["project"]["id"]
assert all(item["run_id"] == l3_record["run"]["id"] for item in l3_record["timeline"])
l3_link = l3_record["report"]["claim_source_links"][0]
l3_evidence_ids = {ev["id"] for src in l3_record["sources"] for ev in src["evidence"]}
assert l3_link["evidence_id"] in l3_evidence_ids

# 3. copy 安全：改返回的 record 不污染 snapshot
l3_mutated = l3_snapshot.to_record()
l3_mutated["timeline"][0]["title"] = "TAMPERED"
assert l3_snapshot.to_record()["timeline"][0]["title"] != "TAMPERED"

# 4. summary_row() 投影正确：列表行只给 resource_count，不给全列表
assert l3_skill.summary_row()["resource_count"] == len(l3_skill.resources)
assert "resources" not in l3_skill.summary_row()
```

What This Proves:

- 一个全新场景也能只靠现有 `from_*` adapter 和产品契约拼出合法快照——九面板齐、跨引用不撒谎、`to_record()` 是独立拷贝、`summary_row()` 只投影列表需要的几列。
- `run.project_id == project.id`、每个 timeline item 的 `run_id == run.id`、report 的 `evidence_id` 落在快照 sources 里——三条跨引用边界都在构造时被强制。
- `summary_row()` 给的是 `resource_count`（一个数）而不是整个 `resources` 列表，正好是列表行渲染需要的投影。

Why This Design:

- L3 不考一个固定答案，而考不变量：只要这四条成立，你拼的快照就是合法、可核对、离线可复现的。
- 全程走 `from_*` 而不手搓面板项，是为了不"悄悄发明第二套数据模型"——面板项永远从真实 domain 对象翻译而来。
- report 的 `claim_source_links` 用 `build_claim_source_links(...)` 从**同一批** evidence/sources 生成，引用链才落在快照里，跨引用校验才会通过。

## Forward Connections

Part 5 的稳定快照契约，是让 FastAPI 和 React 变成"可替换外壳"的前提：只要 `to_record()` 的九面板形状不变，transport 换成别的 web 框架、UI 换成别的前端，产品契约、测试、课程都不用重写。这就是为什么 `research_core.product` 不能 import FastAPI 或 React——依赖只能自上而下。

referential integrity 属于 core，不属于 UI：core 是唯一真相源，任何 transport 拿到的快照都不可能自相矛盾。Part 7 的生产诊断和审计正是靠这一点——它读的每一个快照都已经通过了构造时校验，不需要在诊断层再补一遍"这条 claim 的出处到底存不存在"。

每一个更早的 Part 的契约，都在这里落成一个面板：

- **Part 1 events → timeline**：`RunEvent` 经 `WorkbenchTimelineItem.from_event(...)` 翻译成 timeline 面板，事件顺序被忠实保留（demo 的 `model_request → tool_call → delegate_start → delegate_finish`）。
- **Part 2 evidence chain → sources / report**：`Source`/`Evidence`/`Claim`/`Report` 经 `from_source` / `from_report` + `build_claim_source_links(...)` 翻译成 sources 面板和 report 面板，claim 的出处一路连回真实 evidence。
- **Part 3 memory → memory 面板**：`MemoryRecord` 经 `WorkbenchMemoryItem.from_memory_record(...)` 翻译成 memory 面板，`summary_row()` 给列表行需要的投影。
- **Part 4 delegation → delegation tree**：Part 4 的 delegation result 落成 `WorkbenchDelegationNode`，node id 唯一性由快照构造时校验，delegation tree 展开时每个 child trace 都归属明确。

## Final Takeaway

Workbench 产品代码不是从 UI 装饰开始，而是从一个稳定的快照契约开始：

```text
stable to_record() contract + from_* translation + construct-time referential integrity
```

只要这个 record 稳定、构造时就拒绝矛盾，FastAPI 和 React 就是同一份产品记录外面可替换的壳——测试、文档、API、UI 都能各自演进，而不必把每个 Part 变成一次框架重写。

# Lab 05: Workbench Product

这个 lab 让你把 Chapter 05 的产品契约亲手跑出来：`WorkbenchSnapshot` 是研究员的一页仪表盘，`from_*` adapter 是翻译官，构造时的 referential 校验是契约在替 UI 守边界。你要看到三件事：

1. demo 快照的 record 和 API record 是**同一个形状**——nine 面板一个不少。
2. `to_record()` 每次返回**独立拷贝**——改返回的 record 污染不到 core snapshot。
3. 一个自相矛盾的快照**根本构造不出来**——矛盾在构造时就报错，永远到不了界面。

预计时间：70 到 90 分钟。

## Goal

| Tier | 你做什么 | 你要证明 |
| --- | --- | --- |
| L1 Follow | inspect `build_demo_workbench_snapshot().to_record()`，再用 `TestClient` 打三个 endpoint | 九面板齐、timeline 顺序被保留、API record 与 core `to_record()` 同形 |
| L2 Modify | 改返回的 record 证明 copy 安全；改一个原始对象让 `from_*` 拼出的快照打破一条 referential 校验 | `to_record()` 是独立拷贝；五种矛盾快照都在构造时失败 |
| L3 Design | 不给 skeleton，为一个**新的研究场景**从零拼一个合法快照 | 九面板齐、跨引用合法、copy 安全、`summary_row()` 投影正确 |

## Setup

所有命令默认从 `redesign/` 运行。这个 lab 里既有只用 core 的块，也有要 import `research_api` 的 API 块，所以直接用**同时带 api 和 core** 的 path 打开一个 Python shell（它是 core-only path 的超集）：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run python
```

保持这个 shell 打开。后面的 L1、L2 会复用变量。先确认 focused tests 是绿的：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
```

## L1 Follow: Inspect The Demo Snapshot And Call The API

目标：照着跑一遍，先不要改。你要看到两件事对得上：core 层 `to_record()` 出来的九面板，和 FastAPI transport 搬出来的九面板，是**同一个形状**。

### Step 1: Inspect the demo snapshot record

先看别人拼好的成品快照。`build_demo_workbench_snapshot()` 是一个完整的参照基准：

```python
from research_core.product import build_demo_workbench_snapshot

demo = build_demo_workbench_snapshot()
record = demo.to_record()

print(sorted(record.keys()))
print([item["type"] for item in record["timeline"]])
print(record["run"]["status"])
print(record["memory"][0]["summary_row"]["tags"])
```

Expected output:

```text
['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']
['model_request', 'tool_call', 'delegate_start', 'delegate_finish']
completed
['citation', 'reporting']
```

四行分别证明：九个面板 key 一个不少；timeline 忠实保留了 runtime event 的顺序；run 状态是 `completed`；memory 面板的列表行投影带着原 record 的 tags。

Self-check:

```python
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
assert record["memory"][0]["summary_row"]["tags"] == ["citation", "reporting"]
```

### Step 2: Call the API with TestClient

FastAPI 只是 transport——它把同一个 `to_record()` 照原样搬到 HTTP 上。用 `TestClient` 离线打三个 endpoint（不起真实服务器、不联网）。这一步依赖 `research_api`，所以刚才那个 `apps/api/src:packages/research_core/src` 的 path 是必须的：

```python
from fastapi.testclient import TestClient
from research_api.main import create_app

client = TestClient(create_app())

health = client.get("/health")
snapshot_response = client.get("/api/workbench/snapshot")
timeline_response = client.get("/api/workbench/timeline")

print(health.status_code, health.json())
print(snapshot_response.status_code)
print(sorted(snapshot_response.json().keys()))
print([item["type"] for item in timeline_response.json()])
```

Expected output:

```text
200 {'status': 'ok', 'service': 'research-workbench-api'}
200
['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']
['model_request', 'tool_call', 'delegate_start', 'delegate_finish']
```

API 返回的九个 key，和 Step 1 里 core 层 `to_record()` 的九个 key 完全一致；`/api/workbench/timeline` 就是同一 record 的 `timeline` 切片。transport 没有发明任何新形状。

Self-check:

```python
assert health.json() == {
    "status": "ok",
    "service": "research-workbench-api",
}
assert snapshot_response.status_code == 200
assert timeline_response.status_code == 200
assert timeline_response.json() == snapshot_response.json()["timeline"]
```

### Exercise Feedback - L1 Follow

**Common Errors**:

1. `ModuleNotFoundError: No module named 'research_api'` - 你可能用了 core-only 的 `PYTHONPATH=packages/research_core/src`。API 块要 `PYTHONPATH=apps/api/src:packages/research_core/src`，因为 `research_api` 住在 `apps/api/src`。
2. `ModuleNotFoundError: No module named 'research_core'` - 你可能没有从 `redesign/` 运行。
3. 以为 `/api/workbench/timeline` 会返回和 snapshot 不同的形状 - 它就是 snapshot record 的 `timeline` 切片，transport 不改 contract。

**Failure Output Interpretation**: 如果 `sorted(record.keys())` 少了某个面板，说明快照没组装完整；如果 API 的 key 和 core 的对不上，说明 transport 层偷偷改了形状（这在当前实现里不应该发生）。先分别打印 core 的 `sorted(record.keys())` 和 API 的 `sorted(snapshot_response.json().keys())`，逐个对。

**Where To Go Back**: 回到 Chapter 05 的 "WorkbenchSnapshot 的九个面板槽" 图和 "三层边界：依赖只能往下" 图，确认 core → api → web 的依赖方向和 record 形状契约。

**Why Correct Answer Is Correct**: L1 证明了产品层最小契约：core 层一次 `to_record()` 定义了九面板的稳定形状，FastAPI 只是把它原样搬走。API 和 UI 消费的是**形状契约**，不是某一份具体数据。

## L2 Modify: Copy Safety And Referential Breaks

目标：先预测，再改。L2 分两条线——先证明返回的 record 是独立拷贝（copy 安全），再故意改坏原始对象，看契约在**构造时**怎么挡住五种自相矛盾的快照。每次 Break 都要先回答：这条校验在守哪一层的边界？

### Step 1: Copy safety (predict-then-verify)

先预测：如果你把 API 返回的 record 深层字段改坏，再重新 `GET` 一次 snapshot，第二次拿到的是被污染的值，还是原值？

运行（还在同一个 shell，复用 L1 的 `client` / `snapshot_response`）：

```python
data = snapshot_response.json()
data["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
data["memory"][0]["summary_row"]["tags"].append("mutated")

fresh = client.get("/api/workbench/snapshot").json()
print(fresh["timeline"][0]["metadata"]["tokens"]["prompt"])
print(fresh["memory"][0]["summary_row"]["tags"])
```

Expected output:

```text
128
['citation', 'reporting']
```

改坏 `data` 里的深层字段，重新 `GET` 拿到的仍是原值——证明 `to_record()` 每次返回**独立拷贝**，改它污染不到 core snapshot。产品层因此可以放心让 UI 编辑、排序、过滤返回的 record。

Self-check:

```python
assert fresh["timeline"][0]["metadata"]["tokens"]["prompt"] == 128
assert fresh["memory"][0]["summary_row"]["tags"] == ["citation", "reporting"]
```

### Step 2: Assemble a valid snapshot from raw objects

Break/Fix 之前，先用 `from_*` adapter 从原始 domain 对象拼一个**合法**的临床试验评审快照，作为后面打破的基准。先 import 要用的名字：

```python
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

造原始对象，再用 `from_*` 翻译成面板项，最后拼成快照：

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
print("l2 snapshot assembled")
print(l2_snapshot.to_record()["report"]["claim_source_links"][0]["evidence_id"])
```

Expected output:

```text
l2 snapshot assembled
evidence_efficacy
```

能打印出这两行，说明快照通过了构造时的全部 referential 校验，而且报告的引用链一路连回了真实 evidence。

### Step 3: Break one raw object (predict-then-verify)

现在只改**一个**原始对象：给 timeline 事件一个和 run 对不上的 `run_id`，其它照旧。先预测：`from_event` 会照单翻译这个坏 `run_id`，那么快照构造会成功，还是在跨引用校验时失败？

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
    print(exc)
```

Expected output:

```text
timeline run_id must match run id
```

Diagnosis: 这个 timeline 事件属于 `run_OTHER`，却被塞进 `run_trials` 的快照。`from_event` 只忠实翻译，不会替你改 `run_id`；守边界的是 `WorkbenchSnapshot` 的构造。Fix: timeline 里每个 item 的 `run_id` 都必须等于 `run.id`（用真实事件的 `from_event` 翻译时自然满足）。

### Step 4: Break the other four checks

再逐个打破剩下四条校验，复用上面的 `l2_project` / `l2_run` / `l2_source_item`。每个 Break 块都自己捕获异常，读报错、诊断、再说怎么修。

**Break A — run 的 project_id 对不上 project**。诊断问题：header 会把这个 run 挂在哪个项目下？

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
    print(exc)
```

Expected output:

```text
run project_id must match project id
```

Fix: 让 `run.project_id` 等于 `project.id`。

**Break B — report 引用了快照里不存在的 evidence**。诊断问题：报告说"这条 claim 有出处"，但那条 evidence 不在 `sources` 里，会漏出什么可审计性漏洞？

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
    print(exc)
```

Expected output:

```text
report claim_source_links evidence_id must reference snapshot evidence
```

Fix: report 的每条 `claim_source_links` 的 `evidence_id`，都必须能在快照 sources 的 evidence 里找到（用 `build_claim_source_links` 从同一批 evidence/sources 生成即可，就像 Step 2）。

**Break C — delegation node id 重复**。诊断问题：两个 node 共用一个 id，delegation tree 展开时怎么知道某个 child trace 属于哪个任务？

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
    print(exc)
```

Expected output:

```text
delegation node ids must be unique
```

Fix: 每个 delegation node 的 `id` 保持唯一。

**Break D — eval score 越界**。诊断问题：这个失败发生在哪一层？（提示：它甚至还没进快照。）

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
    print(exc)
```

Expected output:

```text
score must be a number between 0 and 1
```

Fix: score 落在 `0 <= score <= 1`。这条校验在**面板项自己**的构造就失败，比快照更早一层——如果 score 能是 1.5，前端的百分比、进度条、颜色和 eval gate 都会开始撒谎。

Self-check（把两条边界的报错文本对一遍）：

```python
def error_text(build):
    try:
        build()
        return "NO ERROR"
    except ValueError as exc:
        return str(exc)


assert error_text(
    lambda: WorkbenchSnapshot(
        project=l2_project,
        run=WorkbenchRun(
            id="run_trials", project_id="project_WRONG", title="t", question="q"
        ),
    )
) == "run project_id must match project id"
assert error_text(
    lambda: WorkbenchEvalItem(
        id="e", title="t", metric="m", status="passed", score=1.5
    )
) == "score must be a number between 0 and 1"
print("l2 referential checks confirmed")
```

Expected output:

```text
l2 referential checks confirmed
```

### Exercise Feedback - L2 Modify

**Common Errors**:

1. 以为改 `data` 会污染 core snapshot - `to_record()` 每次返回独立拷贝，改返回值影响不到内部对象。
2. 手搓一个 `WorkbenchTimelineItem(...)` 绕过 `from_event` 去"修" `run_id` - 那是在发明第二套数据模型；正确做法是让原始 `RunEvent` 的 `run_id` 就对。
3. 把 eval score 越界当成快照级错误 - 它在面板项构造时就失败，比 `_validate_snapshot_references` 更早。
4. 以为 `report claim_source_links evidence_id must reference snapshot evidence` 是 report 内部错误 - 它是**快照跨引用**错误：evidence 必须出现在快照的 `sources` 里。

**Failure Output Interpretation**: 五条报错各守一层边界——`run project_id must match project id`（project ↔ run）、`timeline run_id must match run id`（run ↔ timeline）、`report claim_source_links evidence_id must reference snapshot evidence`（report ↔ sources 证据链）、`delegation node ids must be unique`（delegation 身份）、`score must be a number between 0 and 1`（单个面板项数值域）。看到某条报错，先问它连的是哪两层。

**Where To Go Back**: 回到 Chapter 05 的 Section 4 "打破 referential integrity" 五个 Break，逐条对照本 lab 的五条；再看 [DEEP] "为什么这重要"——所有校验都在构造时失败，所以矛盾快照根本不存在。

**Why Correct Answer Is Correct**: L2 证明你能区分三种失败层级：单个面板项的域校验（eval score）、快照跨引用校验（其余四条）、以及 transport 的 copy 安全（Step 1）。矛盾快照在构造时就被拒绝，UI 永远不需要处理"半坏的数据"。

## L3 Design: Assemble A New Scenario From Scratch

目标：不给完整 skeleton，你自己为一个**全新的研究场景**从零拼一个合法 `WorkbenchSnapshot`，并证明它满足全部不变量。

场景（换一个和前面完全不同的题目）：**LLM 安全红队评审**。研究员想知道"某个越狱提示是否真的绕过了模型的安全护栏"。你要拼出的快照至少包含：

- 一个 `WorkbenchProject` + 一个 `WorkbenchRun`（`run.project_id` 必须等于 `project.id`）。
- 至少一条 timeline item，用 `WorkbenchTimelineItem.from_event(...)` 从一个 `RunEvent` 翻译，且事件 `run_id` 等于 `run.id`。
- 至少一个 `WorkbenchSourceItem.from_source(...)`，挂一条 `Evidence`，并用 `claim_ids_by_evidence_id` 把 evidence 连到一个 claim。
- 一个 `WorkbenchReport.from_report(...)`，其 `claim_source_links` 用 `build_claim_source_links(...)` 从**同一批** evidence/sources 生成（这样引用链才落在快照里）。
- 至少一条 `WorkbenchMemoryItem.from_memory_record(...)`、一个 `WorkbenchSkillItem`、一个 `WorkbenchEvalItem`（`0 <= score <= 1`）、一个 `WorkbenchDelegationNode`（id 唯一）。

约束：**只能用现有的 `from_*` adapter 和产品契约**，不能新增字段、方法或面板类型；不能手搓面板项绕过 `from_*`。

你要证明的不变量：九面板齐、跨引用全部合法、`to_record()` 返回独立拷贝、`summary_row()` 投影正确。下面是最低自查模板——注意：这段引用你自己发明的 L3 变量（`l3_snapshot` / `l3_record` / `l3_skill`），所以它是**设计验收模板，不是直接粘贴运行的完整示例**；可运行参考答案在 solution 里。

```text
# 假设：l3_snapshot 是你拼的快照，l3_record = l3_snapshot.to_record()，
# l3_skill 是你放进 skills 面板的那个 WorkbenchSkillItem。

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

# 2. 跨引用合法（能 to_record() 就说明构造时校验已通过；再显式验两条关键边界）
assert l3_record["run"]["project_id"] == l3_record["project"]["id"]
assert all(item["run_id"] == l3_record["run"]["id"] for item in l3_record["timeline"])
link = l3_record["report"]["claim_source_links"][0]
evidence_ids = {
    ev["id"] for src in l3_record["sources"] for ev in src["evidence"]
}
assert link["evidence_id"] in evidence_ids

# 3. copy 安全：改返回的 record 不污染 snapshot
mutated = l3_snapshot.to_record()
mutated["timeline"][0]["title"] = "TAMPERED"
assert l3_snapshot.to_record()["timeline"][0]["title"] != "TAMPERED"

# 4. summary_row() 投影正确：列表行只给 resource_count，不是全列表
assert l3_skill.summary_row()["resource_count"] == len(l3_skill.resources)
assert "resources" not in l3_skill.summary_row()
```

### Exercise Feedback - L3 Design

**Common Errors**:

1. 手搓 `WorkbenchEvidenceItem(...)` / `WorkbenchSourceItem(...)` 而不走 `from_*` - 这就是 Chapter 05 [TRAP] 说的"悄悄发明第二套数据模型"。
2. report 的 `claim_source_links` 用了不在 `sources` 里的 evidence - 触发 `report claim_source_links evidence_id must reference snapshot evidence`；一定要用 `build_claim_source_links` 从同一批对象生成。
3. timeline 事件的 `run_id` 忘了对齐 `run.id` - 触发 `timeline run_id must match run id`。
4. 以为改 `to_record()` 的返回值能改到 snapshot - 它是独立拷贝，改不动。

**Failure Output Interpretation**: 如果 `WorkbenchSnapshot(...)` 直接抛 `ValueError`，先读报错属于哪条边界（对照 L2 的五条），再回去改**原始对象**，而不是去改面板项。如果九面板断言失败，说明你漏传了某个 slot——`report` 可以是 `None`，但九个 key 仍要在 `to_record()` 里出现。

**Where To Go Back**: 回到 Chapter 05 的 Section 2 "从原始对象组装一个快照"，那是同款流程的另一个场景（RAG 评测）；把它的 `from_*` 调用顺序当模板，换成你的红队场景。

**Why Correct Answer Is Correct**: L3 不考一个固定答案，而考不变量：九面板齐、跨引用不撒谎、`to_record()` 是独立拷贝、`summary_row()` 只投影列表需要的几列。只要这四条成立，你拼的快照就是一个合法的、可核对的、离线可复现的产品快照。

## Reflection

做完 lab 后，用自己的话回答：

1. 为什么 core 层 `to_record()` 的九面板 key，必须和 `/api/workbench/snapshot` 的九个 key 逐字一致？如果 transport 层擅自加一个 key 会坏掉什么？
2. `to_record()` 为什么必须每次返回独立拷贝，而不是内部对象本身？
3. L2 的五条校验里，哪一条发生在面板项构造、哪四条发生在快照跨引用？为什么 eval score 越界要更早一层失败？
4. 为什么 referential integrity 要在 Python 契约里强制，而不是放到 React 校验里？如果 UI 是唯一做这层检查的地方，会坏掉什么？
5. 你在 L3 里为什么只能用 `from_*` adapter，而不能手搓 `WorkbenchEvidenceItem(...)`？这和"不发明第二套数据模型"有什么关系？

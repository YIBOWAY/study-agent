# Part 5: Workbench Product — 给研究员一个能打开、能核对的工作台

> 接 Part 4。你已经让本地论文研究助手有了 event trail、evidence chain、memory/skill、delegation。Part 5 换一个视角：不再问 "runtime 内部对象长什么样"，而是问 "研究员打开界面时，他能看到、能点、能核对出处的那一页，是从哪里来的、谁保证它不撒谎"。

预计时间：80 到 110 分钟。

## Learner Contract

- **Who this is for**: Beginner Track 和 Engineer Track 都适合。你需要认得 Part 1 的 `RunEvent`、Part 2 的 `Source`/`Evidence`/`Claim`/`Report`、Part 3 的 `MemoryRecord`、Part 4 的 delegation node。
- **Before you start**: 先完成 Part 1 的 Agent Kernel、Part 2 的 evidence chain、Part 3 的 Memory and Skills、Part 4 的 Delegation。
- **You will build**: 一个完全离线的产品快照：从原始 domain 对象出发，用 `from_*` adapter 把它们翻译成面板项，组装成一个 `WorkbenchSnapshot`，再用 `to_record()` 输出 API 和 UI 都能消费的 JSON record。
- **You will be able to explain**: 为什么产品层不能把后端对象原样丢给前端；`from_*` adapter 在翻译什么；`summary_row()` 是给列表渲染的投影；为什么 referential-integrity 校验放在 Python 契约里，而不是 React 里；三层边界为什么只能自上而下依赖。
- **You will prove it works by running**: `PYTHONPATH=apps/api/src:packages/research_core/src uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q`。
- **Offline guarantee**: 全程 deterministic 本地对象；没有 API key、网络、真实 provider、数据库、登录或 websocket streaming。

## 你的本地论文研究助手现在需要：一个可检查的工作台

前四个 Part 之后，研究员信任了这套系统的内部记录。但现在他说了一句很朴素的话：

> "我看不懂代码，也看不懂 event trail 的原始 dict。给我一个能打开、能点、能核对出处的工作台——timeline、证据、报告、记忆、评测，一页都别少。"

把内部对象直接暴露给界面听起来最省事，但工程上马上有两个必须避开的失败：

1. **UI 自己发明一套数据模型**：前端为了好渲染，重新定义 "source" "claim" "score" 的字段。于是同一个 claim，runtime 说它连着 evidence A，UI 却画成连着 evidence B。工作台和运行时开始讲两个故事。
2. **UI 直接读活的内部对象**：前端 import runtime 的 `RunEvent`、`MemoryRecord`，跟着内部重构一起漂移。内部一改字段，界面就悄悄坏掉，而且没人知道哪一层先撒的谎。

Part 5 解决的就是这个问题：给研究员一页**稳定的、可核对的、离线可复现的**工作台快照，但既不发明新数据模型，也不让 UI 直接抱住内部对象。

> [BIG] **大局观**：Part 1-4 教的是 runtime 怎么把工作**做对**并留下记录；Part 5 教的是怎么把这些记录**翻译成产品**而不失真。产品层不是新功能，而是一层受契约保护的翻译。

```text
Local Paper Research Assistant
  [x] Part 1: Agent Kernel, event trail
  [x] Part 2: Research Core, evidence chain
  [x] Part 3: Memory and Skills
  [x] Part 4: Delegation
  [*] Part 5: Workbench Product
      [*] from_* adapters 把 domain 对象翻译成面板项
      [*] WorkbenchSnapshot 是一页稳定的页面契约
      [*] referential integrity 在构造时守边界
      [*] FastAPI/React 只是可替换的外壳
  [ ] Part 6: Framework comparison
  [ ] Part 7: Production readiness
```

## Section 1 [LIGHT Concept]: 仪表盘、快照、翻译官

产品层的心智模型：`WorkbenchSnapshot` 是研究员的**仪表盘**——一页把所有面板拼在一起的稳定契约。`from_*` adapter 是**翻译官**——把工程对象翻译成面板项。referential validation 是**契约在替 UI 守边界**——一个自相矛盾的快照根本构造不出来，所以永远到不了界面。

| System piece | Plain-language model | What to inspect |
| --- | --- | --- |
| raw domain objects | 工程原件（runtime/research/memory 产出） | `RunEvent`, `Source`, `Evidence`, `Claim`, `Report`, `MemoryRecord` |
| `from_*` adapters | 翻译官：把原件翻成面板项 | `WorkbenchTimelineItem.from_event(...)` 等 classmethod |
| `WorkbenchSnapshot` | 仪表盘：一页稳定的页面契约 | 九个面板槽 + 构造时的 referential 校验 |
| `to_record()` | 出片：JSON-compatible 独立拷贝 | 给 FastAPI / React 消费，改它不污染 snapshot |
| `summary_row()` | 列表行投影：面板只需要的几列 | memory / skill / eval item 各有 |

每个 `Workbench*` 面板项翻译自哪个原件、喂给哪个面板：

| Workbench item | Adapts from raw object | Panel it feeds |
| --- | --- | --- |
| `WorkbenchTimelineItem` | `RunEvent`（Part 1） | Run timeline |
| `WorkbenchDelegationNode` | delegation result（Part 4） | Delegation tree |
| `WorkbenchSourceItem` | `Source` + `Evidence`（Part 2） | Sources and evidence |
| `WorkbenchEvidenceItem` | `Evidence`（Part 2） | Sources and evidence |
| `WorkbenchReport` | `Report` + `ClaimSourceLink`（Part 2） | Report editor |
| `WorkbenchMemoryItem` | `MemoryRecord`（Part 3） | Memory panel |
| `WorkbenchSkillItem` | skill package info（Part 3） | Skills panel |
| `WorkbenchEvalItem` | eval result（Part 7 forward） | Eval panel |
| `WorkbenchProject` / `WorkbenchRun` | project/run 元数据 | Header / task composer |

> [DD] **设计决策**：`research_core` 不能 import FastAPI 或 React。如果 core 依赖产品框架，测试、课程、CLI、未来 worker 都会被框架绑死。所以产品契约住在 `research_core.product`，FastAPI 和 React 都只是它下游的可替换外壳。

### 三层边界：依赖只能往下

```text
LAYER 3  React panels (apps/web)
             |  reads JSON only
             v
LAYER 2  FastAPI read endpoints (apps/api)
             |  calls snapshot.to_record()
             v
LAYER 1  research_core.product
             |
   from_* adapters
             |  translate
             v
         WorkbenchSnapshot  --to_record()-->  JSON record
             ^
             |  built from
   raw domain objects: RunEvent / Source / Evidence / Claim / Report / MemoryRecord

  Dependency arrow points DOWN only:
  apps/web -> apps/api -> research_core.product -> runtime/domain
  research_core NEVER imports FastAPI, React, or a provider SDK.
```

### WorkbenchSnapshot 的九个面板槽

```text
WorkbenchSnapshot
  |
  |-- project    : WorkbenchProject          <- project metadata
  |-- run        : WorkbenchRun              <- run metadata (project_id must match project.id)
  |-- timeline   : [WorkbenchTimelineItem]   <- from RunEvent   (run_id must match run.id)
  |-- delegation : [WorkbenchDelegationNode] <- from delegation (node ids unique)
  |-- sources    : [WorkbenchSourceItem]     <- from Source + Evidence
  |-- report     : WorkbenchReport | None    <- from Report + ClaimSourceLink
  |                                             (evidence_id must reference snapshot evidence)
  |-- memory     : [WorkbenchMemoryItem]     <- from MemoryRecord
  |-- skills     : [WorkbenchSkillItem]      <- skill package info
  |-- evals      : [WorkbenchEvalItem]       <- eval result (0 <= score <= 1)

  to_record().keys() (sorted):
  delegation, evals, memory, project, report, run, skills, sources, timeline
```

> [CHECK] **检查一下**：九个面板名要背下来。等下每次 `to_record()` 都必须给出这九个 key，一个不多一个不少。少了某个面板，就说明快照没组装完整。

## Section 2 [FULL Build]: 从原始对象组装一个快照

v1 只教了 `build_demo_workbench_snapshot()`——一个别人拼好的成品。但产品层的重点是**翻译机制**，所以这一节我们从原始对象亲手拼一个 RAG 评测场景的快照。

从 `redesign/` 打开 Python shell（这一节只用 core，所以只要 core 的 path）：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

先 import 所有要用的名字：

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
    build_demo_workbench_snapshot,
)
from research_core.research import (
    Claim,
    Evidence,
    Report,
    ResearchRunStatus,
    Source,
    build_claim_source_links,
)
from research_core.runtime import RunEvent, RunEventType
```

### Build: 先造原始 domain 对象

这些就是前几个 Part 的产出——工程原件，还没有任何产品视角：

```python
source = Source(
    id="source_ragas",
    uri="memory://papers/ragas",
    title="RAGAS: Automated RAG Evaluation",
    content="Faithfulness measures whether an answer stays grounded in retrieved context.",
    metadata={"year": 2023},
)
evidence = Evidence(
    id="evidence_faithfulness",
    source_id=source.id,
    quote="Faithfulness measures whether an answer stays grounded in retrieved context.",
    location="section-3",
    metadata={"confidence": 0.9},
)
claim = Claim(
    id="claim_faithfulness",
    text="Faithfulness scoring catches unsupported RAG answers.",
    evidence_ids=[evidence.id],
)
report = Report(
    id="report_rag_eval",
    run_id="run_rag_eval",
    title="RAG Evaluation Findings",
    summary="Faithfulness and answer-relevance together score a RAG answer.",
    claims=[claim],
)
memory_record = MemoryRecord(
    id="mem_faithfulness_rule",
    kind=MemoryKind.PINNED,
    content="Always report faithfulness before answer relevance.",
    tags=["evaluation", "faithfulness"],
    importance=0.9,
)
```

### Build: 用 from_* adapter 翻译成面板项

`from_*` classmethod 是产品层唯一正确的入口：它接住一个 domain 对象，产出一个面板项，并把原对象的 payload/metadata 一起带过来。

```python
timeline = (
    WorkbenchTimelineItem.from_event(
        RunEvent(
            id="evt_request",
            run_id="run_rag_eval",
            type=RunEventType.MODEL_REQUEST,
            payload={"tokens": {"prompt": 96}},
        ),
        title="Model request",
        summary="Planned which evaluation metrics to compute.",
    ),
    WorkbenchTimelineItem.from_event(
        RunEvent(
            id="evt_tool",
            run_id="run_rag_eval",
            type=RunEventType.TOOL_CALL,
            payload={"tool": "retriever.search", "query": "ragas faithfulness"},
        ),
        title="Tool call",
        summary="Retrieved the RAGAS source passage.",
    ),
)

source_item = WorkbenchSourceItem.from_source(
    source,
    summary="Primary metric definition source.",
    evidence=[evidence],
    claim_ids_by_evidence_id={evidence.id: (claim.id,)},
)
claim_source_links = build_claim_source_links(
    report, evidence=[evidence], sources=[source]
)
report_item = WorkbenchReport.from_report(report, claim_source_links=claim_source_links)
memory_item = WorkbenchMemoryItem.from_memory_record(
    memory_record,
    title="Faithfulness-first rule",
    summary="Pinned rule for metric reporting order.",
)

print(source_item.evidence[0].claim_ids)
print(timeline[0].type.value)
```

Expected output:

```text
('claim_faithfulness',)
model_request
```

第一行证明 `from_source` 把 evidence 翻成了 `WorkbenchEvidenceItem`，并把它连到的 claim id 一起挂上；第二行证明 `from_event` 保留了原 `RunEvent` 的类型。

上面的 `from_source(...)` 内部替你批量调了 `from_evidence`——但它本身也是五个 `from_*` 翻译口之一，可以直接对单条 evidence 用：

```python
from research_core.product import WorkbenchEvidenceItem

evidence_item = WorkbenchEvidenceItem.from_evidence(evidence, claim_ids=(claim.id,))
print(evidence_item.source_id)
print(evidence_item.claim_ids)
```

Expected output:

```text
source_ragas
('claim_faithfulness',)
```

`from_evidence` 直接接住 Part 2 的 `Evidence`，把 `source_id` 原样带过来，再挂上你指定的 claim id。刚才 `from_source(source, evidence=[evidence], claim_ids_by_evidence_id=...)` 做的就是把这个 `from_evidence` 调用替每条 evidence 批处理一遍。

> [TRAP] **常见误解**：不要为了组装快照去手写一个 `WorkbenchEvidenceItem(...)` 而绕过 `from_*`。`from_evidence` / `from_source` / `from_event` / `from_report` / `from_memory_record` 才是唯一保证字段和原件对齐的翻译口。手搓面板项，就是在悄悄发明第二套数据模型——正是我们要避开的失败 1。

### Build: 组装成一页 snapshot

剩下三个面板项（delegation / skill / eval）没有独立 domain 原件，直接用产品契约构造。delegation 之所以直接构造、没有 `from_delegation`，是因为 Part 4 产出的是一棵结果**树**而不是单条记录，没有单一 domain 源可翻译。然后把九个槽拼成 `WorkbenchSnapshot`：

```python
project = WorkbenchProject(id="project_rag_eval", title="RAG Evaluation Survey")
run = WorkbenchRun(
    id="run_rag_eval",
    project_id=project.id,
    title="Score RAG answers",
    question="Which metrics prove a RAG answer is trustworthy?",
    status=ResearchRunStatus.COMPLETED,
)
delegation = (
    WorkbenchDelegationNode(
        id="task_metric_review",
        title="Metric review",
        role="evaluation-reviewer",
        status="completed",
        run_id="run_child_metric_review",
        summary="Confirmed each metric maps to a source-backed claim.",
    ),
)
skill = WorkbenchSkillItem(
    id="skill_metric_check",
    title="Metric check",
    name="metric-check",
    description="Checks that each eval metric has a source-backed claim.",
    resources=("references/metrics.md", "scripts/check_metrics.py"),
)
eval_item = WorkbenchEvalItem(
    id="eval_faithfulness",
    title="Faithfulness coverage",
    metric="faithfulness",
    status="passed",
    score=0.92,
)

snapshot = WorkbenchSnapshot(
    project=project,
    run=run,
    timeline=timeline,
    delegation=delegation,
    sources=(source_item,),
    report=report_item,
    memory=(memory_item,),
    skills=(skill,),
    evals=(eval_item,),
)
print("snapshot built")
```

Expected output:

```text
snapshot built
```

能打印出这行，说明快照通过了构造时的全部 referential 校验（Section 4 会故意打破它们）。

## Section 3 [FULL Inspect]: 读面板与列表行投影

有了 `snapshot`，产品层要输出的是 `to_record()`——一个 JSON-compatible 的独立拷贝。

```python
record = snapshot.to_record()
print(sorted(record.keys()))
print([item["type"] for item in record["timeline"]])
print(record["sources"][0]["evidence"][0]["claim_ids"])
print(record["report"]["claim_source_links"][0]["source_title"])
print(record["timeline"][0]["metadata"])
```

Expected output:

```text
['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']
['model_request', 'tool_call']
['claim_faithfulness']
RAGAS: Automated RAG Evaluation
{'tokens': {'prompt': 96}}
```

这五行分别证明：九个面板都在；timeline 保留了 runtime event 的顺序；evidence 还连着它支撑的 claim；report 的引用链能一路回溯到 source 标题；`from_event` 带过来的 payload 在 record 里被 thaw 成普通 dict。

> [CHECK] **检查一下**：`record["timeline"]` 的顺序是 `['model_request', 'tool_call']`——和我们构造 `timeline` 元组的顺序一致。timeline 面板的价值就在于**忠实保留 runtime 顺序**，产品层不能重排事件。

### summary_row(): 列表只要几列

面板列表不需要每项的全部字段，只要几列就能渲染一行。`summary_row()` 就是这个投影：

```python
print(memory_item.summary_row())
print(skill.summary_row())
print(eval_item.summary_row())
```

Expected output:

```text
{'id': 'mem_faithfulness_rule', 'title': 'Faithfulness-first rule', 'kind': 'pinned', 'importance': 0.9, 'tags': ['evaluation', 'faithfulness']}
{'id': 'skill_metric_check', 'title': 'Metric check', 'name': 'metric-check', 'status': 'loaded', 'resource_count': 2}
{'id': 'eval_faithfulness', 'title': 'Faithfulness coverage', 'metric': 'faithfulness', 'status': 'passed', 'score': 0.92}
```

注意 skill 的 `summary_row()` 给的是 `resource_count`（`len(resources)`），不是 resources 全列表。列表行只需要"有几个资源"，详情面板才展开全部——这就是投影的意义。

### 参考基准：预置的 demo 快照

`build_demo_workbench_snapshot()` 是一个别人拼好的完整快照，适合当参照基准：

```python
demo = build_demo_workbench_snapshot()
print(sorted(demo.to_record().keys()))
print([item["type"] for item in demo.to_record()["timeline"]])
```

Expected output:

```text
['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']
['model_request', 'tool_call', 'delegate_start', 'delegate_finish']
```

demo 的九个 key 和我们手拼的完全一样——因为它们受同一个契约约束。区别只是 demo 的 timeline 多了两个 delegation 事件。

## Section 4 [BREAK/FIX]: 打破 referential integrity

产品层最有价值的保护，是 `WorkbenchSnapshot` 在**构造时**就校验跨引用一致性。一个自相矛盾的快照根本构造不出来，所以永远到不了 UI。下面逐个打破——每个 Break 块都自己捕获异常，读报错、诊断、再说怎么修。

复用前面的 `project`（`project_rag_eval`）和 `run`（`run_rag_eval`）。

### Break 1: run 的 project_id 对不上 project

```python
try:
    WorkbenchSnapshot(
        project=project,
        run=WorkbenchRun(
            id="run_rag_eval",
            project_id="project_WRONG",
            title="Score RAG answers",
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

Diagnosis: run 声称属于 `project_WRONG`，但快照里的 project 是 `project_rag_eval`。如果放行，header 会显示一个 run 挂在错误的项目下。Fix: 让 `run.project_id` 等于 `project.id`。

### Break 2: timeline 的 run_id 对不上 run

```python
try:
    WorkbenchSnapshot(
        project=project,
        run=run,
        timeline=[
            WorkbenchTimelineItem(
                id="t_orphan",
                run_id="run_OTHER",
                type=RunEventType.MODEL_REQUEST,
                title="Orphan event",
            )
        ],
    )
except ValueError as exc:
    print(exc)
```

Expected output:

```text
timeline run_id must match run id
```

Diagnosis: 这个 timeline 事件属于 `run_OTHER`，却被塞进 `run_rag_eval` 的快照。放行的话，timeline 面板会把别的 run 的事件画进这一页。Fix: timeline 里每个 item 的 `run_id` 都必须等于 `run.id`（用 `from_event` 翻译真实事件时自然满足）。

### Break 3: report 引用了快照里不存在的 evidence

```python
from research_core.research import ClaimSourceLink

dangling_link = ClaimSourceLink(
    claim_id="claim_faithfulness",
    claim_text="Faithfulness scoring catches unsupported RAG answers.",
    evidence_id="evidence_MISSING",
    source_id="source_ragas",
    source_title="RAGAS",
    source_uri="memory://papers/ragas",
    quote="q",
)
try:
    WorkbenchSnapshot(
        project=project,
        run=run,
        report=WorkbenchReport(
            id="report_rag_eval",
            run_id=run.id,
            title="RAG Evaluation Findings",
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

Diagnosis: 报告的引用链指向 `evidence_MISSING`，但这条 evidence 不在快照的 `sources` 里。这正是 "报告说有出处，出处却不在" 的可审计性漏洞。Fix: report 的每条 `claim_source_links` 的 `evidence_id`，都必须能在快照 sources 的 evidence 里找到（用 `build_claim_source_links` 从同一批 evidence/sources 生成即可）。

### Break 4: delegation node id 重复

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
    WorkbenchSnapshot(project=project, run=run, delegation=[node_a, node_b])
except ValueError as exc:
    print(exc)
```

Expected output:

```text
delegation node ids must be unique
```

Diagnosis: 两个 delegation node 共用 `task_dup`。delegation tree 靠 node id 定位和展开，id 撞车后就无法可靠地说"这个 child trace 属于哪个任务"。Fix: 每个 delegation node 的 `id` 保持唯一。

### Break 5: eval score 越界

```python
try:
    WorkbenchEvalItem(
        id="eval_bad",
        title="Bad eval",
        metric="faithfulness",
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

Diagnosis: 这个失败发生在**面板项自己**的构造，甚至还没进快照。如果 score 能是 1.5，前端的百分比、进度条、颜色和 eval gate 都会开始撒谎。Fix: score 落在 `0 <= score <= 1`。

> [DEEP] **为什么这重要**：这五个校验有一个共同点——它们都在**构造时**失败，而不是在渲染时。这意味着一个自相矛盾的快照**根本不存在**，UI 永远不需要处理"半坏的数据"。把这条防线放在 Python 契约里而不是 React 里，是因为 FastAPI 和 React 都是可替换外壳；换掉任何一个，这层保护都还在。

## Section 5 [FULL Transport]: FastAPI 与 React 边界

`to_record()` 出片之后，FastAPI 只是把它照原样搬到 HTTP 上。API 是 transport，不改 contract。

这一节要用到 `apps/api`，所以 path 要同时带上 api 和 core：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run python
```

用 FastAPI 的 `TestClient` 离线打这三个 endpoint（不起真实服务器、不联网）：

```python
from fastapi.testclient import TestClient
from research_api.main import create_app

client = TestClient(create_app())
print(client.get("/health").json())
snapshot_record = client.get("/api/workbench/snapshot").json()
print(sorted(snapshot_record.keys()))
timeline_record = client.get("/api/workbench/timeline").json()
print(timeline_record == snapshot_record["timeline"])
print([item["type"] for item in timeline_record])
```

Expected output:

```text
{'status': 'ok', 'service': 'research-workbench-api'}
['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']
True
['model_request', 'tool_call', 'delegate_start', 'delegate_finish']
```

`/api/workbench/snapshot` 返回的九个 key，和 core 层 `to_record()` 完全一致；`/api/workbench/timeline` 就是同一 record 的 `timeline` 切片。transport 没有发明任何新形状。

### 复制安全：改 record 不会污染 snapshot

产品层允许 UI 编辑、排序、过滤返回的 record。前提是 `to_record()` 每次都返回**独立拷贝**：

```python
from research_core.product import build_demo_workbench_snapshot

demo_snapshot = build_demo_workbench_snapshot()
mutated = demo_snapshot.to_record()
mutated["timeline"][0]["metadata"]["tokens"]["prompt"] = 999
print(demo_snapshot.to_record()["timeline"][0]["metadata"]["tokens"]["prompt"])
```

Expected output:

```text
128
```

改坏 `mutated` 里的深层字段，重新 `to_record()` 拿到的仍是原值 `128`——证明 record 是 plain copy，改它污染不到 core snapshot。

> [DD] **设计决策：fallback fixture 必须和 API record 同形**。React app 在 API 不可用时会退回一个本地 fallback fixture。这个 fixture 不是"随便造点假数据"，它必须和 `/api/workbench/snapshot` 的 record 形状逐字段一致（同样九个面板、同样字段名）。否则 UI 用 fixture 测试全绿，一接真实 API 就崩——因为 UI 依赖的是 record 的**形状契约**，不是某一份具体数据。fixture 与 record 同形，等于把"不发明第二套数据模型"这条规矩钉在前端。

## Section 6 [DEEP Reflect]: 每个 Part 都在这里显形

Workbench 的九个面板不是凭空来的，它们正是前面每个 Part 的对象翻译过来的：

- Part 1 的 `RunEvent` → `timeline` 面板（`from_event`）。
- Part 2 的 evidence chain（`Source`/`Evidence`/`Claim`/`Report`）→ `sources` 和 `report` 面板（`from_source` / `from_report` + `build_claim_source_links`）。
- Part 3 的 `MemoryRecord` → `memory` 面板（`from_memory_record`），skill package → `skills` 面板。
- Part 4 的 delegation → `delegation` 树面板。
- Part 7 会接上：一次 production run 必须能从**同一批 record** 复盘出来。referential integrity 现在守的边界，就是 Part 7 审计和诊断的地基。

> [CHECK] **回接 Part 2**：Part 2 里 claim 必须连着 evidence、evidence 必须连着 source。Part 5 的 `report claim_source_links evidence_id must reference snapshot evidence` 校验，就是把这条证据链的完整性一路守到了产品边界——报告面板永远不会展示一条"查无出处"的引用。

## Eval Gate

从 `redesign/` 运行（API 相关测试需要 api path）：

```bash
PYTHONPATH=apps/api/src:packages/research_core/src uv run pytest tests/research_core/test_workbench_snapshot.py tests/apps/test_workbench_api.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=packages/research_core/src uv run ruff check packages/research_core/src/research_core/product apps/api/src
cd apps/web && npm run build
```

核心自查：

> 这段自查沿用本章前面同一个 Python shell session 的 `snapshot` 和 `record` 等变量；如果你另开了新 shell，先把 Section 2、Section 3 的 setup 重新跑一遍再执行。

```python
assert sorted(snapshot.to_record().keys()) == [
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
assert [item["type"] for item in snapshot.to_record()["timeline"]] == [
    "model_request",
    "tool_call",
]
assert skill.summary_row()["resource_count"] == 2
assert record["report"]["claim_source_links"][0]["evidence_id"] == (
    record["sources"][0]["evidence"][0]["id"]
)
print("eval gate self-check passed")
```

Expected output:

```text
eval gate self-check passed
```

## Reflection

继续 Lab 05 前，用自己的话回答：

1. 为什么产品层要用 `from_*` adapter 翻译，而不是让 UI 直接读 `RunEvent` / `MemoryRecord`？
2. `summary_row()` 和 `to_record()` 各自服务哪种界面需求？为什么 skill 列表行只给 `resource_count` 而不是全部 resources？
3. **Tradeoff**：为什么 referential integrity 要在 Python snapshot 契约里强制，而不是放到 React 校验里？如果 UI 是唯一做这层检查的地方，会坏掉什么？
4. `to_record()` 为什么必须返回独立拷贝，而不是内部对象本身？
5. 如果未来要加数据库或真实 provider，应该接在三层的哪一层，为什么不能塞进 `research_core.product`？

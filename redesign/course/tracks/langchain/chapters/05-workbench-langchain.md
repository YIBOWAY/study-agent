# Part 5: Workbench Product（LangChain 轨）

> 接 Part 4。runtime 对象已经够用；研究员要的是**能打开、能核对**的一页工作台。本轨用 `WorkbenchSnapshot` 把 LC 域对象翻译成 JSON 契约，**不 import** `research_core.product`，也不在本 Part 接真实 React。

预计时间：60–90 分钟。

## Learner Contract

- **你会构建**：从 `AgentStep` / `PaperDoc` / `ResearchReport` / memory / skill 组装 `WorkbenchSnapshot`，输出 `to_record()`。
- **你会解释**：为什么产品层不能让 UI 发明第二套模型；referential integrity 为什么在构造时失败；九个面板 key 是什么。
- **你怎么验收**：`uv run pytest packages/langchain_course/tests/test_workbench.py -q`（离线）。
- **诚实边界**：教学 snapshot，不是完整 Workbench SPA；与主课 `apps/web` 形状**语义对齐**，类型不共享。

## 与 handwritten 对照

| Handwritten (`research_core`) | 本轨 (`langchain_course`) |
| --- | --- |
| `WorkbenchSnapshot` | 同名教学类型 |
| `WorkbenchTimelineItem.from_event(RunEvent)` | `WorkbenchTimelineItem.from_step(AgentStep)` |
| `from_*` adapters | `from_paper` / `from_report` / `from_note` / `from_manifest` |
| `to_record()` 九面板 | 同 key 集合 |
| FastAPI / React 外壳 | 本 Part 不接；只保证 JSON record |

> [DD] **为何不直接复用 research_core.product？** 并行轨零 import。形状一致是为了对照学习，不是为了运行时共享。

## Section 1：问题钩子

研究员说：

> 别给我 raw steps dict，给我 timeline、sources、report 一页。

两个坑：

1. UI 自己发明 claim/source 字段 → 和 runtime 讲两个故事  
2. UI 直接 import 内部 dataclass → 内部一改，界面悄悄坏  

```text
AgentStep / PaperDoc / Report / MemoryNote / SkillManifest
        |
   from_* adapters
        v
  WorkbenchSnapshot  --to_record()-->  JSON panels
```

```text
bad internal object --X--> UI guesses a repair
validated adapter    ---> snapshot ---> UI only renders
```

九个 `to_record()` keys：`project, run, timeline, delegation, sources, report, memory, skills, evals`。

## Section 2 [BUILD]：demo snapshot

```bash
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_course.workbench import build_demo_snapshot

snap = build_demo_snapshot()
rec = snap.to_record()
print(sorted(rec.keys()))
assert rec["run"]["project_id"] == rec["project"]["id"]
assert len(rec["timeline"]) >= 1
assert rec["report"]["links"][0]["source_id"] == "paper_1"
```

## Section 3 [BUILD]：从 AgentStep 做 timeline

```python
from langchain_course.agent_kernel import AgentStep
from langchain_course.workbench import (
    WorkbenchProject,
    WorkbenchRun,
    WorkbenchSnapshot,
    WorkbenchTimelineItem,
)

project = WorkbenchProject(id="p1", title="LC Workbench")
run = WorkbenchRun(
    id="r1",
    project_id="p1",
    title="demo",
    question="Why cite?",
)
steps = [
    AgentStep(kind="model_request", payload={"step": "plan"}),
    AgentStep(kind="tool_call", payload={"tool": "keyword_search"}),
]
timeline = tuple(
    WorkbenchTimelineItem.from_step(s, run_id=run.id, index=i)
    for i, s in enumerate(steps)
)
snap = WorkbenchSnapshot(project=project, run=run, timeline=timeline)
assert snap.to_record()["timeline"][1]["type"] == "tool_call"
```

> [TRAP] **run.project_id 必须等于 project.id**；timeline 的 `run_id` 必须等于 `run.id`；report link 的 `source_id` 必须出现在 sources 里——否则构造时 raise，而不是把坏数据交给 UI。

## Section 4 [INSPECT]：从外到内检查 record

```python
record = snap.to_record()
panel_counts = {
    "timeline": len(record["timeline"]),
    "sources": len(record["sources"]),
    "memory": len(record["memory"]),
    "skills": len(record["skills"]),
}
print(panel_counts)
assert record["run"]["id"] == "r1"
assert record["timeline"][0]["run_id"] == record["run"]["id"]
```

> [CHECK] UI 可以排序、折叠和筛选，但不应该补造 source、claim 或 run id。

## Section 5 [BREAK / FIX]：让引用故意断掉

```python
from langchain_course.workbench import WorkbenchError

try:
    WorkbenchSnapshot(
        project=project,
        run=WorkbenchRun(
            id="bad-run",
            project_id="another-project",
            title="broken",
            question="Why cite?",
        ),
    )
except WorkbenchError as exc:
    assert "project_id" in str(exc)
```

修复原则：回到产生错误 id 的 adapter；不要在 `to_record()` 或前端里替换它。

> [DD] Part 5 不需要新的 LangChain orchestration primitive。它学习的是框架
> 输出如何跨过产品边界；这也是为什么 LC callback/steps 必须先变成稳定 panel。

## Eval gate

```bash
uv run pytest packages/langchain_course/tests/test_workbench.py -q
```

## Section 6 [REFLECT]：迁移问题

1. 如果前端可以“修好”坏 snapshot，产品诚实性会怎样？  
2. 本轨 timeline 基于 `AgentStep.kind`，与 handwritten `RunEventType` 对照时你会看什么、不看什么？  
3. 如果将来 Part 1 从手写 loop 换成 LangChain `create_agent`，哪个 adapter
   最可能变化，哪个 JSON panel 不应该变化？

下一章 Part 6：用真实 LC 体验回看 build-vs-adopt 评分。

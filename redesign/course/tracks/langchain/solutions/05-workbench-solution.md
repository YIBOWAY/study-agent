# Solution 05 — Workbench（LangChain 轨）

## 参考要点

- 九个 panel keys 固定；`to_record()` 必须齐全。
- `from_step` 用 `run_id` + `index` 生成稳定 timeline id。
- 构造期校验：project/run 对齐、timeline run_id、report link 的 source 存在。

## L3 示例骨架

```python
from langchain_course.memory import MemoryKind, MemoryNote
from langchain_course.paper_fixtures import default_paper_docs
from langchain_course.research import ClaimLink, EvidenceItem, ResearchReport
from langchain_course.workbench import (
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReportPanel,
    WorkbenchRun,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
)

docs = default_paper_docs()
evidence = [
    EvidenceItem(id="e1", source_id=docs[0].id, quote=docs[0].content[:80])
]
project = WorkbenchProject(id="p", title="lab")
run = WorkbenchRun(id="r", project_id="p", title="t", question="q")
report = ResearchReport(id="rep", title="t", summary="s")
link = ClaimLink(
    claim_id="c1",
    evidence_id="e1",
    source_id=docs[0].id,
    source_uri=docs[0].uri,
    source_title=docs[0].title,
    quote=evidence[0].quote,
)
note = MemoryNote(id="m1", kind=MemoryKind.FACT, content="Cite everything.")
snap = WorkbenchSnapshot(
    project=project,
    run=run,
    sources=tuple(WorkbenchSourceItem.from_paper(d, evidence=evidence) for d in docs),
    report=WorkbenchReportPanel.from_report(report, links=[link]),
    memory=(WorkbenchMemoryItem.from_note(note),),
)
assert "sources" in snap.to_record()
```

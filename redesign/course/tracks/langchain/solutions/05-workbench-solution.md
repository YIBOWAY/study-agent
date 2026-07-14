# Solution 05 — Workbench（LangChain 轨）

## 参考要点

- 九个 panel keys 固定；`to_record()` 必须齐全。
- `from_step` 用 `run_id` + `index` 生成稳定 timeline id。
- 构造期校验：project/run 对齐、timeline run_id、report link 的 source 存在。

## L1/L2 为什么正确

- 九个 key 是消费者合同；空 panel 允许，缺 key 不允许。
- timeline id 同时含 run 与 index，使同一 run 内可排序，又不会把两次 run 混合。
- 构造期失败把错误留在 adapter 边界；若等到 React 渲染才发现，已经无法判断
  是 runtime、API 还是 UI 造错了数据。

常见错误：只断言 `json.dumps(record)` 成功。可序列化只说明类型兼容，不说明
`claim → evidence → source` 引用完整。

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

## L3 设计反馈

正确答案不要求字段与参考实现逐字相同，但必须证明：run 属于 project、timeline
属于 run、report link 指向 sources、memory 来自 policy 允许的记录。若 learners
在前端补 source，回看 Chapter 05 的产品边界图。

## 与 handwritten 的关系

handwritten 和 LC 轨可以共享九面板语义，不能共享 Python 类型。这样将来
LangChain 执行面升级时，只需替换 adapter，不必重写 UI 的领域语言。

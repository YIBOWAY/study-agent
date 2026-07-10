# Solution 02 — Evidence Chain（LangChain 轨）

## L1 Retrieve / Supported claim

- `default_paper_docs()` 提供三篇本地 fixture；`citation grounding` 命中 `paper_1` 最强。
- `build_claim_links` 展开 claim × evidence_ids，填入 source 元数据。
- `to_record()` 便于打印/JSON；教学检查优先用字段断言。

## L2 Two claims

```python
from langchain_course.paper_fixtures import default_paper_docs
from langchain_course.research import (
    ClaimItem,
    EvidenceItem,
    ResearchReport,
    build_claim_links,
)

docs = default_paper_docs()
evidence = [
    EvidenceItem(
        id="evidence_1",
        source_id="paper_1",
        quote="RAG evaluation should report retrieval quality and citation grounding.",
    ),
    EvidenceItem(
        id="evidence_2",
        source_id="paper_2",
        quote="Citation mapping connects every report claim to a quote, source URI, and paper title.",
    ),
]
report = ResearchReport(
    id="report_2",
    title="Two-claim notes",
    summary="Both claims grounded.",
    claims=[
        ClaimItem(id="claim_1", text="Grounding matters for RAG eval.", evidence_ids=["evidence_1"]),
        ClaimItem(id="claim_2", text="Mapping ties claims to quotes.", evidence_ids=["evidence_2"]),
    ],
)
links = build_claim_links(report, evidence=evidence, docs=docs)
assert len(links) == 2
uris = {link.source_uri for link in links}
assert "paper://citation-mapping" in uris
assert "paper://rag-evaluation-survey" in uris
```

## L3 Break / policy

```python
from langchain_course.research import ClaimItem, ResearchChainError, ResearchReport, build_claim_links
from langchain_course.paper_fixtures import default_paper_docs

docs = default_paper_docs()
try:
    build_claim_links(
        ResearchReport(
            id="r", title="t", summary="s",
            claims=[ClaimItem(id="c", text="x", evidence_ids=["nope"])],
        ),
        evidence=[],
        docs=docs,
    )
except ResearchChainError as exc:
    assert "missing evidence" in str(exc)

try:
    build_claim_links(
        ResearchReport(
            id="r", title="t", summary="s",
            claims=[ClaimItem(id="c", text="x", evidence_ids=[])],
        ),
        evidence=[],
        docs=docs,
    )
except ResearchChainError as exc:
    assert "no evidence_ids" in str(exc)
```

**政策讨论参考**：若允许假设 claim，应显式 `status="hypothesis"` / `support="none"`，并在 UI 标红；**不要**用空 `evidence_ids` 表示“已完成研究”。Lab 默认拒绝 empty，是为了训练“可审计默认”。

## 与 handwritten 的差异（有意）

- 无 `SourceIngestor` ID 自动分配；fixture 自带稳定 `paper_N` id。
- 无 embedding；keyword 足够教 grounding 纪律。
- 不共享 Python 类型，避免框架轨与产品 core 缠在一起。

## 为何正确

断言证明的是 **link 完整性**，不是文笔。这与主课 Part 2 的 citation 纪律一致，只是用 LC 轨自己的记录类型表达。

# Lab 02 — Evidence Chain（LangChain 轨）

接 Chapter 02。证明 claim 能回到本地 paper quote。

预计时间：45–60 分钟。

## Setup

```bash
uv sync --group langchain-course
PYTHONPATH=packages/langchain_course/src uv run python
```

```python
from langchain_course.paper_fixtures import default_paper_docs
from langchain_course.research import (
    ClaimItem,
    EvidenceItem,
    KeywordRetriever,
    ResearchChainError,
    ResearchReport,
    build_claim_links,
    format_context_block,
)
```

## Exercise 1 (L1 Follow): Retrieve

```python
docs = default_paper_docs()
hits = KeywordRetriever(docs).search("citation grounding", limit=2)
assert hits[0].source_id == "paper_1"
assert hits[0].score > 0
```

## Exercise 2 (L1 Follow): Supported claim

```python
evidence = [
    EvidenceItem(
        id="evidence_1",
        source_id="paper_1",
        quote="RAG evaluation should report retrieval quality and citation grounding.",
        location="sentence 1",
    )
]
report = ResearchReport(
    id="report_1",
    title="RAG Evaluation Notes",
    summary="Grounding keeps reports auditable.",
    claims=[
        ClaimItem(
            id="claim_1",
            text="RAG evaluation reports should preserve citation grounding.",
            evidence_ids=["evidence_1"],
        )
    ],
)
links = build_claim_links(report, evidence=evidence, docs=docs)
rec = links[0].to_record()
assert rec["claim_id"] == "claim_1"
assert rec["source_id"] == "paper_1"
assert "citation grounding" in rec["quote"]
```

## Exercise 2B (L1 Follow): LangChain Document + Retriever

把同一批 `PaperDoc` 转为 LangChain `Document`，再用
`LangChainPaperRetriever.from_papers(...).invoke("citation grounding")` 检索。
断言第一条 `metadata["source_id"] == "paper_1"`。

**即时反馈**：若只返回 `SearchHit`，你仍在纯 Python 教学层，没有跨入
LangChain Retriever 合同。

## Exercise 3 (L2 Modify): Second paper claim

1. 对 `paper_2` 建 `evidence_2`（quote 含 “Citation mapping”）。
2. report 含两条 claim，分别绑 `evidence_1` 与 `evidence_2`。
3. 断言 `len(links) == 2`，source_uri 集合包含 `paper://citation-mapping`。
4. 把 retriever 传给 `build_research_context_runnable`，检查输出同时保留
   `question/documents/context`，并用 `get_graph()` 检查组合节点。

## Exercise 4 (L3 Design): Break and policy

1. 触发 missing evidence 与 empty evidence_ids，捕获 `ResearchChainError`。
2. 设计：若产品允许“暂无出处的假设 claim”，你会加什么字段/状态，而不是静默空 `evidence_ids`？写 3–5 句，并说明为何 lab 默认拒绝 empty。
3. 删除一个 `Document.metadata.source_id`，解释为什么 Runnable 仍可能运行，
   但证据链产品合同已经损坏。

## Offline gate

```bash
uv run pytest packages/langchain_course/tests/test_research.py -q
```

## Optional：context + live draft（非门禁）

```python
print(format_context_block(docs)[:300])
# 有 .env 时再调用 deepseek；仍须 build_claim_links 校验你手写/整理后的 claim
```

## 对照

Solution：[../solutions/02-evidence-chain-solution.md](../solutions/02-evidence-chain-solution.md)

from __future__ import annotations

import pytest
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


def test_keyword_retriever_ranks_citation_query() -> None:
    docs = default_paper_docs()
    hits = KeywordRetriever(docs).search("citation grounding", limit=2)
    assert len(hits) >= 1
    assert hits[0].source_id == "paper_1"
    assert hits[0].score > 0


def test_build_claim_links_happy_path() -> None:
    docs = default_paper_docs()
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
        summary="Citation grounding keeps reports auditable.",
        claims=[
            ClaimItem(
                id="claim_1",
                text="RAG evaluation reports should preserve citation grounding.",
                evidence_ids=["evidence_1"],
            )
        ],
    )
    links = build_claim_links(report, evidence=evidence, docs=docs)
    assert len(links) == 1
    record = links[0].to_record()
    assert record["claim_id"] == "claim_1"
    assert record["evidence_id"] == "evidence_1"
    assert record["source_id"] == "paper_1"
    assert record["source_uri"] == "paper://rag-evaluation-survey"
    assert "citation grounding" in record["quote"]


def test_build_claim_links_missing_evidence() -> None:
    docs = default_paper_docs()
    report = ResearchReport(
        id="report_1",
        title="t",
        summary="s",
        claims=[ClaimItem(id="c1", text="x", evidence_ids=["missing"])],
    )
    with pytest.raises(ResearchChainError, match="missing evidence"):
        build_claim_links(report, evidence=[], docs=docs)


def test_build_claim_links_rejects_unsupported_claim() -> None:
    docs = default_paper_docs()
    report = ResearchReport(
        id="report_1",
        title="t",
        summary="s",
        claims=[ClaimItem(id="c1", text="x", evidence_ids=[])],
    )
    with pytest.raises(ResearchChainError, match="no evidence_ids"):
        build_claim_links(report, evidence=[], docs=docs)


def test_format_context_block_includes_titles() -> None:
    docs = default_paper_docs()
    block = format_context_block(docs[:2])
    assert "RAG Evaluation Survey" in block
    assert "paper_1" in block

"""Part 2: local evidence chain for the LangChain track.

Framework-native research records for teaching citation grounding. This is not
`research_core.research` and must not import it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough


class ResearchChainError(ValueError):
    """Raised when claim/evidence/source links are incomplete or inconsistent."""


@dataclass(frozen=True, slots=True)
class PaperDoc:
    id: str
    uri: str
    title: str
    content: str

    def to_record(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    id: str
    source_id: str
    quote: str
    location: str = ""

    def to_record(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClaimItem:
    id: str
    text: str
    evidence_ids: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResearchReport:
    id: str
    title: str
    summary: str
    claims: list[ClaimItem] = field(default_factory=list)

    def to_record(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "claims": [c.to_record() for c in self.claims],
        }


@dataclass(frozen=True, slots=True)
class ClaimLink:
    claim_id: str
    evidence_id: str
    source_id: str
    source_uri: str
    source_title: str
    quote: str

    def to_record(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchHit:
    source_id: str
    score: float
    snippet: str

    def to_record(self) -> dict[str, object]:
        return asdict(self)


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN.finditer(text)}


class KeywordRetriever:
    """Offline keyword retriever over local PaperDoc fixtures."""

    def __init__(self, docs: list[PaperDoc]) -> None:
        self._docs = list(docs)

    def search(self, query: str, *, limit: int = 3) -> list[SearchHit]:
        if limit < 1:
            return []
        q_tokens = _tokens(query)
        if not q_tokens:
            return []
        hits: list[SearchHit] = []
        for doc in self._docs:
            hay = _tokens(f"{doc.title} {doc.content}")
            overlap = q_tokens & hay
            if not overlap:
                continue
            score = float(len(overlap)) / float(len(q_tokens))
            snippet = doc.content[:160]
            hits.append(
                SearchHit(source_id=doc.id, score=score, snippet=snippet)
            )
        hits.sort(key=lambda h: (-h.score, h.source_id))
        return hits[:limit]


def paper_docs_to_documents(docs: list[PaperDoc]) -> list[Document]:
    """Convert course records at the framework boundary.

    `PaperDoc` remains the stable, inspectable course record. `Document` is the
    LangChain-native value that flows through retrievers and Runnables.
    """
    return [
        Document(
            page_content=doc.content,
            metadata={
                "source_id": doc.id,
                "source_uri": doc.uri,
                "title": doc.title,
            },
        )
        for doc in docs
    ]


class LangChainPaperRetriever(BaseRetriever):
    """Deterministic `BaseRetriever` over local LangChain Documents."""

    documents: tuple[Document, ...]
    k: int = 3

    @classmethod
    def from_papers(
        cls,
        docs: list[PaperDoc],
        *,
        k: int = 3,
    ) -> LangChainPaperRetriever:
        if k < 1:
            raise ResearchChainError("retriever k must be >= 1")
        return cls(documents=tuple(paper_docs_to_documents(docs)), k=k)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager  # callbacks are managed by BaseRetriever.invoke
        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        ranked: list[tuple[float, str, Document]] = []
        for document in self.documents:
            title = str(document.metadata.get("title", ""))
            overlap = query_tokens & _tokens(f"{title} {document.page_content}")
            if not overlap:
                continue
            score = len(overlap) / len(query_tokens)
            source_id = str(document.metadata.get("source_id", ""))
            ranked.append((score, source_id, document))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [document for _, _, document in ranked[: self.k]]


def documents_to_context(documents: list[Document], *, max_chars: int = 1200) -> str:
    chunks: list[str] = []
    used = 0
    for document in documents:
        source_id = str(document.metadata.get("source_id", "unknown"))
        title = str(document.metadata.get("title", "Untitled"))
        piece = f"[{source_id}] {title}\n{document.page_content}\n"
        if chunks and used + len(piece) > max_chars:
            break
        chunks.append(piece)
        used += len(piece)
    return "\n".join(chunks).strip()


def build_research_context_runnable(
    retriever: BaseRetriever,
) -> Runnable[dict[str, Any], dict[str, Any]]:
    """Compose question -> BaseRetriever -> inspectable prompt context with LCEL."""

    question = RunnableLambda(lambda item: str(item["question"]))
    retrieve = question | retriever

    def _attach_context(item: dict[str, Any]) -> dict[str, Any]:
        documents = list(item["documents"])
        return {
            **item,
            "documents": documents,
            "context": documents_to_context(documents),
        }

    return RunnablePassthrough.assign(documents=retrieve) | RunnableLambda(
        _attach_context
    )


def build_claim_links(
    report: ResearchReport,
    *,
    evidence: list[EvidenceItem],
    docs: list[PaperDoc],
) -> list[ClaimLink]:
    """Map each claim's evidence ids to source metadata.

    Raises ResearchChainError if evidence is missing, source is missing, or a
    claim has no evidence ids.
    """
    evidence_by_id = {item.id: item for item in evidence}
    docs_by_id = {doc.id: doc for doc in docs}
    links: list[ClaimLink] = []

    for claim in report.claims:
        if not claim.evidence_ids:
            raise ResearchChainError(
                f"claim {claim.id!r} has no evidence_ids; unsupported claim"
            )
        for evidence_id in claim.evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                raise ResearchChainError(
                    f"claim {claim.id!r} references missing evidence {evidence_id!r}"
                )
            doc = docs_by_id.get(item.source_id)
            if doc is None:
                raise ResearchChainError(
                    f"evidence {evidence_id!r} references missing source "
                    f"{item.source_id!r}"
                )
            links.append(
                ClaimLink(
                    claim_id=claim.id,
                    evidence_id=item.id,
                    source_id=doc.id,
                    source_uri=doc.uri,
                    source_title=doc.title,
                    quote=item.quote,
                )
            )
    return links


def format_context_block(docs: list[PaperDoc], *, max_chars: int = 1200) -> str:
    """Format local docs into a single context string for a chat prompt."""
    chunks: list[str] = []
    used = 0
    for doc in docs:
        piece = f"[{doc.id}] {doc.title}\n{doc.content}\n"
        if used + len(piece) > max_chars and chunks:
            break
        chunks.append(piece)
        used += len(piece)
    return "\n".join(chunks).strip()

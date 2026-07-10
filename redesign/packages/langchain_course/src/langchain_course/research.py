"""Part 2: local evidence chain for the LangChain track.

Framework-native research records for teaching citation grounding. This is not
`research_core.research` and must not import it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field


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

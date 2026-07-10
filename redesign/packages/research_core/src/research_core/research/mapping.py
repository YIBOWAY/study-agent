from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from research_core.research.entities import Claim, Evidence, Report, Source, _require_non_empty


@dataclass(frozen=True, slots=True)
class ClaimSourceLink:
    claim_id: str
    claim_text: str
    evidence_id: str
    source_id: str
    source_title: str
    source_uri: str
    quote: str
    location: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("claim_id", self.claim_id)
        _require_non_empty("claim_text", self.claim_text)
        _require_non_empty("evidence_id", self.evidence_id)
        _require_non_empty("source_id", self.source_id)
        _require_non_empty("source_title", self.source_title)
        _require_non_empty("source_uri", self.source_uri)
        _require_non_empty("quote", self.quote)

    def to_record(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "source_uri": self.source_uri,
            "quote": self.quote,
            "location": self.location,
        }


def build_claim_source_links(
    report: Report,
    evidence: Sequence[Evidence],
    sources: Sequence[Source],
) -> tuple[ClaimSourceLink, ...]:
    if not isinstance(report, Report):
        raise ValueError("report must be a Report object")
    evidence_by_id = _index_evidence(evidence)
    source_by_id = _index_sources(sources)

    links: list[ClaimSourceLink] = []
    for claim in report.claims:
        if not claim.evidence_ids:
            raise ValueError(f"claim {claim.id!r} must reference at least one evidence id")
        for evidence_id in claim.evidence_ids:
            try:
                evidence_item = evidence_by_id[evidence_id]
            except KeyError as exc:
                raise ValueError(
                    f"claim {claim.id!r} references missing evidence {evidence_id!r}"
                ) from exc
            try:
                source = source_by_id[evidence_item.source_id]
            except KeyError as exc:
                raise ValueError(
                    f"evidence {evidence_item.id!r} references missing source "
                    f"{evidence_item.source_id!r}"
                ) from exc
            links.append(_link_for(claim, evidence_item, source))
    return tuple(links)


def _index_evidence(evidence: Sequence[Evidence]) -> dict[str, Evidence]:
    evidence_by_id: dict[str, Evidence] = {}
    for evidence_item in evidence:
        if not isinstance(evidence_item, Evidence):
            raise ValueError("evidence must contain Evidence objects")
        if evidence_item.id in evidence_by_id:
            raise ValueError(f"duplicate evidence id: {evidence_item.id}")
        evidence_by_id[evidence_item.id] = evidence_item
    return evidence_by_id


def _index_sources(sources: Sequence[Source]) -> dict[str, Source]:
    source_by_id: dict[str, Source] = {}
    for source in sources:
        if not isinstance(source, Source):
            raise ValueError("sources must contain Source objects")
        if source.id in source_by_id:
            raise ValueError(f"duplicate source id: {source.id}")
        source_by_id[source.id] = source
    return source_by_id


def _link_for(claim: Claim, evidence: Evidence, source: Source) -> ClaimSourceLink:
    return ClaimSourceLink(
        claim_id=claim.id,
        claim_text=claim.text,
        evidence_id=evidence.id,
        source_id=source.id,
        source_title=source.title,
        source_uri=source.uri,
        quote=evidence.quote,
        location=evidence.location,
    )

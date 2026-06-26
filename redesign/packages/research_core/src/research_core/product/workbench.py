from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any, TypeVar

from research_core.delegation import DelegationStatus
from research_core.memory import MemoryKind, MemoryRecord
from research_core.research import (
    Claim,
    ClaimSourceLink,
    Evidence,
    ResearchRunStatus,
    Source,
    build_claim_source_links,
)
from research_core.research import (
    Report as ResearchReport,
)
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.immutability import freeze_json_value, thaw_json_value

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class WorkbenchProject:
    id: str
    title: str
    description: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchRun:
    id: str
    project_id: str
    title: str
    question: str
    status: ResearchRunStatus | str = ResearchRunStatus.PLANNED
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("title", self.title)
        _require_non_empty("question", self.question)
        try:
            status = ResearchRunStatus(self.status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in ResearchRunStatus)
            raise ValueError(f"status must be one of: {allowed_statuses}") from exc
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "question": self.question,
            "status": self.status.value,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchTimelineItem:
    id: str
    run_id: str
    type: RunEventType | str
    title: str
    summary: str = ""
    timestamp: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("run_id", self.run_id)
        _require_non_empty("title", self.title)
        try:
            event_type = RunEventType(self.type)
        except ValueError as exc:
            allowed_types = ", ".join(event_type.value for event_type in RunEventType)
            raise ValueError(f"type must be one of: {allowed_types}") from exc
        object.__setattr__(self, "type", event_type)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_event(
        cls,
        event: RunEvent,
        *,
        title: str,
        summary: str = "",
        timestamp: str = "",
    ) -> WorkbenchTimelineItem:
        if not isinstance(event, RunEvent):
            raise ValueError("event must be a RunEvent")
        return cls(
            id=event.id,
            run_id=event.run_id,
            type=event.type,
            title=title,
            summary=summary,
            timestamp=timestamp,
            metadata=event.to_record()["payload"],
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "type": self.type.value,
            "title": self.title,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchDelegationNode:
    id: str
    title: str
    role: str
    status: DelegationStatus | str
    run_id: str
    summary: str = ""
    parent_id: str = ""
    children: Sequence[WorkbenchDelegationNode] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("role", self.role)
        _require_non_empty("run_id", self.run_id)
        try:
            status = DelegationStatus(self.status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in DelegationStatus)
            raise ValueError(f"status must be one of: {allowed_statuses}") from exc
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "children",
            _tuple_of_objects("children", self.children, WorkbenchDelegationNode),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "role": self.role,
            "status": self.status.value,
            "run_id": self.run_id,
            "summary": self.summary,
            "parent_id": self.parent_id,
            "children": [child.to_record() for child in self.children],
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class _WorkbenchEvidenceItem:
    id: str
    source_id: str
    quote: str
    claim_ids: Sequence[str] = ()
    summary: str = ""
    location: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("source_id", self.source_id)
        _require_non_empty("quote", self.quote)
        object.__setattr__(
            self,
            "claim_ids",
            _tuple_of_non_empty_strings("claim_ids", self.claim_ids),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_evidence(
        cls,
        evidence: Evidence,
        *,
        claim_ids: Sequence[str] = (),
    ) -> _WorkbenchEvidenceItem:
        if not isinstance(evidence, Evidence):
            raise ValueError("evidence must be an Evidence object")
        return cls(
            id=evidence.id,
            source_id=evidence.source_id,
            quote=evidence.quote,
            claim_ids=claim_ids,
            summary=evidence.summary,
            location=evidence.location,
            metadata=evidence.metadata,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "quote": self.quote,
            "claim_ids": list(self.claim_ids),
            "summary": self.summary,
            "location": self.location,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSourceItem:
    id: str
    title: str
    uri: str
    summary: str = ""
    evidence: Sequence[_WorkbenchEvidenceItem] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("uri", self.uri)
        object.__setattr__(
            self,
            "evidence",
            _tuple_of_objects("evidence", self.evidence, _WorkbenchEvidenceItem),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_source(
        cls,
        source: Source,
        *,
        summary: str = "",
        evidence: Sequence[Evidence] = (),
        claim_ids_by_evidence_id: Mapping[str, Sequence[str]] | None = None,
    ) -> WorkbenchSourceItem:
        if not isinstance(source, Source):
            raise ValueError("source must be a Source object")
        claim_ids_by_evidence_id = (
            {} if claim_ids_by_evidence_id is None else claim_ids_by_evidence_id
        )
        return cls(
            id=source.id,
            title=source.title,
            uri=source.uri,
            summary=summary,
            evidence=tuple(
                _WorkbenchEvidenceItem.from_evidence(
                    evidence_item,
                    claim_ids=claim_ids_by_evidence_id.get(evidence_item.id, ()),
                )
                for evidence_item in evidence
            ),
            metadata=source.metadata,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "uri": self.uri,
            "summary": self.summary,
            "evidence": [evidence.to_record() for evidence in self.evidence],
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchReport:
    id: str
    run_id: str
    title: str
    summary: str
    claim_source_links: Sequence[ClaimSourceLink] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("run_id", self.run_id)
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        object.__setattr__(
            self,
            "claim_source_links",
            _tuple_of_objects(
                "claim_source_links",
                self.claim_source_links,
                ClaimSourceLink,
            ),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_report(
        cls,
        report: ResearchReport,
        *,
        claim_source_links: Sequence[ClaimSourceLink],
    ) -> WorkbenchReport:
        if not isinstance(report, ResearchReport):
            raise ValueError("report must be a Report object")
        return cls(
            id=report.id,
            run_id=report.run_id,
            title=report.title,
            summary=report.summary,
            claim_source_links=claim_source_links,
            metadata=report.metadata,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "title": self.title,
            "summary": self.summary,
            "claim_source_links": [
                link.to_record() for link in self.claim_source_links
            ],
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchMemoryItem:
    id: str
    title: str
    kind: MemoryKind | str
    content: str
    summary: str = ""
    tags: Sequence[str] = ()
    importance: float = 0.5
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("content", self.content)
        try:
            kind = MemoryKind(self.kind)
        except ValueError as exc:
            allowed_kinds = ", ".join(kind.value for kind in MemoryKind)
            raise ValueError(f"kind must be one of: {allowed_kinds}") from exc
        _require_score("importance", self.importance)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "tags", _tuple_of_non_empty_strings("tags", self.tags))
        object.__setattr__(self, "importance", float(self.importance))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_memory_record(
        cls,
        record: MemoryRecord,
        *,
        title: str,
        summary: str = "",
    ) -> WorkbenchMemoryItem:
        if not isinstance(record, MemoryRecord):
            raise ValueError("record must be a MemoryRecord")
        return cls(
            id=record.id,
            title=title,
            kind=record.kind,
            content=record.content,
            summary=summary,
            tags=record.tags,
            importance=record.importance,
            metadata=record.metadata,
        )

    def summary_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind.value,
            "importance": self.importance,
            "tags": list(self.tags),
        }

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind.value,
            "content": self.content,
            "summary": self.summary,
            "tags": list(self.tags),
            "importance": self.importance,
            "summary_row": self.summary_row(),
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSkillItem:
    id: str
    title: str
    name: str
    description: str = ""
    status: str = "loaded"
    resources: Sequence[str] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("name", self.name)
        _require_non_empty("status", self.status)
        object.__setattr__(
            self,
            "resources",
            _tuple_of_non_empty_strings("resources", self.resources),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def summary_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "name": self.name,
            "status": self.status,
            "resource_count": len(self.resources),
        }

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "resources": list(self.resources),
            "summary_row": self.summary_row(),
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchEvalItem:
    id: str
    title: str
    metric: str
    status: str
    score: float
    details: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("metric", self.metric)
        _require_non_empty("status", self.status)
        _require_score("score", self.score)
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def summary_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "metric": self.metric,
            "status": self.status,
            "score": self.score,
        }

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "metric": self.metric,
            "status": self.status,
            "score": self.score,
            "details": self.details,
            "summary_row": self.summary_row(),
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSnapshot:
    project: WorkbenchProject
    run: WorkbenchRun
    timeline: Sequence[WorkbenchTimelineItem] = ()
    delegation: Sequence[WorkbenchDelegationNode] = ()
    sources: Sequence[WorkbenchSourceItem] = ()
    report: WorkbenchReport | None = None
    memory: Sequence[WorkbenchMemoryItem] = ()
    skills: Sequence[WorkbenchSkillItem] = ()
    evals: Sequence[WorkbenchEvalItem] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.project, WorkbenchProject):
            raise ValueError("project must be a WorkbenchProject")
        if not isinstance(self.run, WorkbenchRun):
            raise ValueError("run must be a WorkbenchRun")
        if self.report is not None and not isinstance(self.report, WorkbenchReport):
            raise ValueError("report must be a WorkbenchReport")
        object.__setattr__(
            self,
            "timeline",
            _tuple_of_objects("timeline", self.timeline, WorkbenchTimelineItem),
        )
        object.__setattr__(
            self,
            "delegation",
            _tuple_of_objects("delegation", self.delegation, WorkbenchDelegationNode),
        )
        object.__setattr__(
            self,
            "sources",
            _tuple_of_objects("sources", self.sources, WorkbenchSourceItem),
        )
        object.__setattr__(
            self,
            "memory",
            _tuple_of_objects("memory", self.memory, WorkbenchMemoryItem),
        )
        object.__setattr__(
            self,
            "skills",
            _tuple_of_objects("skills", self.skills, WorkbenchSkillItem),
        )
        object.__setattr__(
            self,
            "evals",
            _tuple_of_objects("evals", self.evals, WorkbenchEvalItem),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "project": self.project.to_record(),
            "run": self.run.to_record(),
            "timeline": [item.to_record() for item in self.timeline],
            "delegation": [node.to_record() for node in self.delegation],
            "sources": [source.to_record() for source in self.sources],
            "report": None if self.report is None else self.report.to_record(),
            "memory": [item.to_record() for item in self.memory],
            "skills": [item.to_record() for item in self.skills],
            "evals": [item.to_record() for item in self.evals],
        }


def build_demo_workbench_snapshot() -> WorkbenchSnapshot:
    project = WorkbenchProject(
        id="project_workbench_demo",
        title="Research Agent Workbench",
        description="Deterministic local snapshot for the Phase 5 product surface.",
        metadata={"owner": "research_core.product"},
    )
    run = WorkbenchRun(
        id="run_workbench_demo",
        project_id=project.id,
        title="Workbench snapshot contract demo",
        question="How should a research workbench preserve traceability?",
        status=ResearchRunStatus.COMPLETED,
        metadata={"mode": "demo"},
    )

    timeline = tuple(
        WorkbenchTimelineItem.from_event(event, title=title, summary=summary)
        for event, title, summary in (
            (
                RunEvent(
                    id="evt_model_request",
                    run_id=run.id,
                    type=RunEventType.MODEL_REQUEST,
                    payload={"model": "demo-research-model", "tokens": {"prompt": 128}},
                ),
                "Model request",
                "Asked the planner to identify evidence requirements.",
            ),
            (
                RunEvent(
                    id="evt_tool_call",
                    run_id=run.id,
                    type=RunEventType.TOOL_CALL,
                    payload={
                        "tool": "retriever.search",
                        "query": "workbench claim source links",
                    },
                ),
                "Tool call",
                "Retrieved source material for the report claim.",
            ),
            (
                RunEvent(
                    id="evt_delegate_start",
                    run_id=run.id,
                    type=RunEventType.DELEGATE_START,
                    payload={
                        "task_id": "task_source_review",
                        "child_run_id": "run_child_source_review",
                    },
                ),
                "Delegate start",
                "Started a focused source-review child run.",
            ),
            (
                RunEvent(
                    id="evt_delegate_finish",
                    run_id=run.id,
                    type=RunEventType.DELEGATE_FINISH,
                    payload={
                        "task_id": "task_source_review",
                        "child_run_id": "run_child_source_review",
                        "status": "completed",
                    },
                ),
                "Delegate finish",
                "Merged the child review back into the parent run.",
            ),
        )
    )

    delegation = (
        WorkbenchDelegationNode(
            id="task_source_review",
            title="Source review",
            role="evidence-reviewer",
            status=DelegationStatus.COMPLETED,
            run_id="run_child_source_review",
            summary="Confirmed that each report claim keeps a source-backed link.",
            metadata={"parent_run_id": run.id},
        ),
    )

    source = Source(
        id="source_claim_links",
        uri="memory://workbench/claim-links",
        title="Workbench Contract Notes",
        content="Every report claim keeps an evidence link back to a source.",
        metadata={"kind": "demo"},
    )
    evidence = Evidence(
        id="evidence_claim_links",
        source_id=source.id,
        quote="Every report claim keeps an evidence link back to a source.",
        location="note-1",
        metadata={"confidence": 1.0},
    )
    report_claim = Claim(
        id="claim_1",
        text="Citation-backed workbench snapshots make research auditable.",
        evidence_ids=[evidence.id],
    )
    research_report = ResearchReport(
        id="report_workbench_demo",
        run_id=run.id,
        title="Workbench Snapshot Demo",
        summary=(
            "The snapshot exposes timeline, delegation, sources, report, memory, "
            "skills, and eval panels."
        ),
        claims=[report_claim],
    )
    claim_source_links = build_claim_source_links(
        research_report,
        evidence=[evidence],
        sources=[source],
    )

    sources = (
        WorkbenchSourceItem.from_source(
            source,
            summary="Contract note used to prove claim-source continuity.",
            evidence=[evidence],
            claim_ids_by_evidence_id={evidence.id: (report_claim.id,)},
        ),
    )
    report = WorkbenchReport.from_report(
        research_report,
        claim_source_links=claim_source_links,
    )

    memory = (
        WorkbenchMemoryItem.from_memory_record(
            MemoryRecord(
                id="mem_citation_rule",
                kind=MemoryKind.PINNED,
                content="Always preserve citation links in research reports.",
                tags=["citation", "reporting"],
                importance=0.95,
            ),
            title="Citation rule",
            summary="Pinned rule that keeps report claims auditable.",
        ),
        WorkbenchMemoryItem.from_memory_record(
            MemoryRecord(
                id="mem_workbench_preference",
                kind=MemoryKind.SEMANTIC,
                content="The workbench should show dense operational panels.",
                tags=["product"],
                importance=0.8,
            ),
            title="Workbench preference",
            summary="Durable product preference recalled for the UI.",
        ),
    )

    skills = (
        WorkbenchSkillItem(
            id="skill_source_mapping",
            title="Source mapping",
            name="source-mapping",
            description="Checks that report claims keep source links.",
            status="loaded",
            resources=("references/claim-source-links.md", "scripts/check_links.py"),
        ),
    )
    evals = (
        WorkbenchEvalItem(
            id="eval_claim_links",
            title="Claim links",
            metric="claim_source_coverage",
            status="passed",
            score=1.0,
            details="All report claims include source-backed evidence links.",
        ),
    )

    return WorkbenchSnapshot(
        project=project,
        run=run,
        timeline=timeline,
        delegation=delegation,
        sources=sources,
        report=report,
        memory=memory,
        skills=skills,
        evals=evals,
    )


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _freeze_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return freeze_json_value(dict(metadata))


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or isinstance(values, Mapping):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must not contain blank values")
    return result


def _tuple_of_objects(
    name: str,
    values: Sequence[_T],
    expected_type: type[_T],
) -> tuple[_T, ...]:
    result = tuple(values)
    if any(not isinstance(value, expected_type) for value in result):
        raise ValueError(f"{name} must contain {expected_type.__name__} objects")
    return result


def _require_score(name: str, value: float) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not isfinite(value)
        or not 0 <= value <= 1
    ):
        raise ValueError(f"{name} must be a number between 0 and 1")

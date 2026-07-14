"""Part 5: workbench snapshot surface for the LangChain track.

Projects teaching domain objects into a JSON-compatible page contract.
Does not import research_core.product and is not a product FastAPI layer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from langchain_course.agent_kernel import AgentStep
from langchain_course.memory import MemoryNote
from langchain_course.research import ClaimLink, EvidenceItem, PaperDoc, ResearchReport
from langchain_course.skills import SkillManifest


class WorkbenchError(ValueError):
    """Raised when a workbench snapshot is inconsistent or incomplete."""


_PANEL_KEYS = (
    "project",
    "run",
    "timeline",
    "delegation",
    "sources",
    "report",
    "memory",
    "skills",
    "evals",
)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise WorkbenchError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class WorkbenchProject:
    id: str
    title: str
    description: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchRun:
    id: str
    project_id: str
    title: str
    question: str
    status: str = "completed"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("title", self.title)
        _require_non_empty("question", self.question)
        _require_non_empty("status", self.status)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "question": self.question,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchTimelineItem:
    id: str
    run_id: str
    type: str
    title: str
    summary: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("run_id", self.run_id)
        _require_non_empty("type", self.type)
        _require_non_empty("title", self.title)

    @classmethod
    def from_step(
        cls,
        step: AgentStep,
        *,
        run_id: str,
        index: int,
        title: str | None = None,
        summary: str = "",
    ) -> WorkbenchTimelineItem:
        if not isinstance(step, AgentStep):
            raise WorkbenchError("step must be an AgentStep")
        if index < 0:
            raise WorkbenchError("index must be >= 0")
        kind = step.kind
        return cls(
            id=f"{run_id}_step_{index}",
            run_id=run_id,
            type=kind,
            title=title or kind.replace("_", " ").title(),
            summary=summary,
            metadata=dict(step.payload),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "type": self.type,
            "title": self.title,
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchDelegationNode:
    id: str
    title: str
    role: str
    status: str
    run_id: str
    summary: str = ""
    parent_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("role", self.role)
        _require_non_empty("status", self.status)
        _require_non_empty("run_id", self.run_id)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "role": self.role,
            "status": self.status,
            "run_id": self.run_id,
            "summary": self.summary,
            "parent_id": self.parent_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSourceItem:
    id: str
    uri: str
    title: str
    evidence_ids: tuple[str, ...] = ()
    summary: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("uri", self.uri)
        _require_non_empty("title", self.title)

    @classmethod
    def from_paper(
        cls,
        doc: PaperDoc,
        *,
        evidence: Sequence[EvidenceItem] = (),
    ) -> WorkbenchSourceItem:
        evidence_ids = tuple(item.id for item in evidence if item.source_id == doc.id)
        return cls(
            id=doc.id,
            uri=doc.uri,
            title=doc.title,
            evidence_ids=evidence_ids,
            summary=doc.content[:120],
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "uri": self.uri,
            "title": self.title,
            "evidence_ids": list(self.evidence_ids),
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchReportPanel:
    id: str
    title: str
    summary: str
    claim_ids: tuple[str, ...] = ()
    links: tuple[dict[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)

    @classmethod
    def from_report(
        cls,
        report: ResearchReport,
        *,
        links: Sequence[ClaimLink] = (),
    ) -> WorkbenchReportPanel:
        return cls(
            id=report.id,
            title=report.title,
            summary=report.summary,
            claim_ids=tuple(claim.id for claim in report.claims),
            links=tuple(link.to_record() for link in links),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "claim_ids": list(self.claim_ids),
            "links": [dict(link) for link in self.links],
        }


@dataclass(frozen=True, slots=True)
class WorkbenchMemoryItem:
    id: str
    kind: str
    content: str
    pinned: bool = False
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("kind", self.kind)
        _require_non_empty("content", self.content)

    @classmethod
    def from_note(cls, note: MemoryNote) -> WorkbenchMemoryItem:
        return cls(
            id=note.id,
            kind=note.kind.value,
            content=note.content,
            pinned=note.pinned,
            tags=tuple(note.tags),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content": self.content,
            "pinned": self.pinned,
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSkillItem:
    name: str
    description: str
    references: tuple[str, ...] = ()
    entrypoint: str = "SKILL.md"

    def __post_init__(self) -> None:
        _require_non_empty("name", self.name)
        _require_non_empty("description", self.description)

    @classmethod
    def from_manifest(cls, manifest: SkillManifest) -> WorkbenchSkillItem:
        return cls(
            name=manifest.name,
            description=manifest.description,
            references=tuple(manifest.references),
            entrypoint=manifest.entrypoint,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "references": list(self.references),
            "entrypoint": self.entrypoint,
        }


@dataclass(frozen=True, slots=True)
class WorkbenchEvalItem:
    id: str
    metric: str
    passed: bool
    score: float = 0.0
    detail: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("metric", self.metric)
        if not isinstance(self.passed, bool):
            raise WorkbenchError("passed must be a boolean")
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise WorkbenchError("score must be a number")
        if self.score < 0.0 or self.score > 1.0:
            raise WorkbenchError("score must be between 0 and 1 inclusive")

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metric": self.metric,
            "passed": self.passed,
            "score": float(self.score),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class WorkbenchSnapshot:
    project: WorkbenchProject
    run: WorkbenchRun
    timeline: Sequence[WorkbenchTimelineItem] = ()
    delegation: Sequence[WorkbenchDelegationNode] = ()
    sources: Sequence[WorkbenchSourceItem] = ()
    report: WorkbenchReportPanel | None = None
    memory: Sequence[WorkbenchMemoryItem] = ()
    skills: Sequence[WorkbenchSkillItem] = ()
    evals: Sequence[WorkbenchEvalItem] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.project, WorkbenchProject):
            raise WorkbenchError("project must be a WorkbenchProject")
        if not isinstance(self.run, WorkbenchRun):
            raise WorkbenchError("run must be a WorkbenchRun")
        if self.report is not None and not isinstance(self.report, WorkbenchReportPanel):
            raise WorkbenchError("report must be a WorkbenchReportPanel or None")
        object.__setattr__(self, "timeline", tuple(self.timeline))
        object.__setattr__(self, "delegation", tuple(self.delegation))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "memory", tuple(self.memory))
        object.__setattr__(self, "skills", tuple(self.skills))
        object.__setattr__(self, "evals", tuple(self.evals))
        _validate_snapshot(self)

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


def _validate_snapshot(snapshot: WorkbenchSnapshot) -> None:
    if snapshot.run.project_id != snapshot.project.id:
        raise WorkbenchError(
            f"run.project_id {snapshot.run.project_id!r} does not match "
            f"project.id {snapshot.project.id!r}"
        )
    for item in snapshot.timeline:
        if item.run_id != snapshot.run.id:
            raise WorkbenchError(
                f"timeline item {item.id!r} run_id {item.run_id!r} "
                f"does not match run.id {snapshot.run.id!r}"
            )
    seen_node_ids: set[str] = set()
    for node in snapshot.delegation:
        if node.id in seen_node_ids:
            raise WorkbenchError(f"duplicate delegation node id {node.id!r}")
        seen_node_ids.add(node.id)
        if node.run_id != snapshot.run.id:
            raise WorkbenchError(
                f"delegation node {node.id!r} run_id does not match run.id"
            )
    source_ids = {source.id for source in snapshot.sources}
    if snapshot.report is not None:
        for link in snapshot.report.links:
            source_id = link.get("source_id", "")
            if source_id and source_id not in source_ids:
                raise WorkbenchError(
                    f"report link references unknown source_id {source_id!r}"
                )


def build_demo_snapshot() -> WorkbenchSnapshot:
    """Deterministic demo snapshot for Part 5 labs (offline)."""
    project = WorkbenchProject(
        id="project_lc_demo",
        title="LangChain Track Workbench Demo",
        description="Offline snapshot for teaching product translation.",
        metadata={"track": "langchain"},
    )
    run = WorkbenchRun(
        id="run_lc_demo",
        project_id=project.id,
        title="Citation grounding demo",
        question="Why does citation grounding matter for RAG evaluation?",
        status="completed",
    )
    steps = (
        AgentStep(kind="model_request", payload={"step": "plan"}),
        AgentStep(kind="tool_call", payload={"tool": "keyword_search"}),
        AgentStep(kind="final", payload={"text": "Citation grounding keeps reports auditable."}),
    )
    timeline = tuple(
        WorkbenchTimelineItem.from_step(step, run_id=run.id, index=i)
        for i, step in enumerate(steps)
    )
    docs = [
        PaperDoc(
            id="paper_1",
            uri="paper://rag-evaluation-survey",
            title="RAG Evaluation Survey",
            content="RAG evaluation should report citation grounding.",
        )
    ]
    evidence = [
        EvidenceItem(
            id="evidence_1",
            source_id="paper_1",
            quote="RAG evaluation should report citation grounding.",
        )
    ]
    report = ResearchReport(
        id="report_1",
        title="Demo report",
        summary="Citation grounding keeps reports auditable.",
        claims=[],
    )
    link = ClaimLink(
        claim_id="claim_1",
        evidence_id="evidence_1",
        source_id="paper_1",
        source_uri=docs[0].uri,
        source_title=docs[0].title,
        quote=evidence[0].quote,
    )
    return WorkbenchSnapshot(
        project=project,
        run=run,
        timeline=timeline,
        sources=(WorkbenchSourceItem.from_paper(docs[0], evidence=evidence),),
        report=WorkbenchReportPanel.from_report(report, links=[link]),
        memory=(),
        skills=(),
        evals=(
            WorkbenchEvalItem(
                id="eval_has_citation",
                metric="has_citation",
                passed=True,
                score=1.0,
                detail="demo link present",
            ),
        ),
    )

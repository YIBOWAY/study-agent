"""Reference Capstone agent: offline local paper research assistant.

This module is a teaching artifact under course/capstone/solution/.
It composes public research_core APIs from Parts 1-7. It is not product code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_core.delegation import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationRuntime,
    DelegationStatus,
    DelegationTask,
    filter_tools_for_role,
)
from research_core.memory import (
    MemoryEngine,
    MemoryKind,
    MemoryRecallPolicy,
    MemoryRecord,
    MemoryWritePolicy,
)
from research_core.product import (
    WorkbenchDelegationNode,
    WorkbenchEvalItem,
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReport,
    WorkbenchRun,
    WorkbenchSkillItem,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
)
from research_core.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    JsonlRunEventStore,
    RunDiagnostics,
    SandboxPolicy,
)
from research_core.research import (
    Claim,
    Evidence,
    FakeRetriever,
    Report,
    ResearchRunStatus,
    SourceIngestor,
    SourceInput,
    build_claim_source_links,
)
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
)
from research_core.skills import SkillRuntime
from research_core.testing import FakeModel, FakeModelResponse

CAPSTONE_ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = CAPSTONE_ROOT / "paper_fixtures" / "papers.json"
SKILL_PATH = CAPSTONE_ROOT / "skills" / "citation-check"
TRAJECTORY_PATH = Path(__file__).resolve().parent / "trajectory.jsonl"

RESEARCH_QUESTION = (
    "Does citation grounding matter for trustworthy RAG evaluation, "
    "and what should a local research assistant remember or delegate?"
)
RUN_ID = "run_capstone"
PROJECT_ID = "project_capstone"
CHILD_RUN_ID = "run_capstone_review"


@dataclass(frozen=True, slots=True)
class CapstoneResult:
    sources: tuple[Any, ...]
    evidence: tuple[Evidence, ...]
    report: Report
    links: tuple[Any, ...]
    memory_records: tuple[MemoryRecord, ...]
    skill_name: str
    skill_reference: str
    run_events: tuple[Any, ...]
    event_types: list[str]
    delegation_status: str
    snapshot_record: dict[str, Any]
    diagnostics_record: dict[str, Any]
    jsonl_run_ids: tuple[str, ...]
    approval_retrieval: str
    approval_shell: str
    network_allowed: bool
    final_answer: str


def load_paper_inputs(path: Path = PAPERS_PATH) -> list[SourceInput]:
    raw_papers = json.loads(path.read_text(encoding="utf-8"))
    return [
        SourceInput(
            uri=paper["uri"],
            title=paper["title"],
            content=paper["content"],
            metadata={
                "year": paper.get("year"),
                "topics": tuple(paper.get("topics", ())),
            },
        )
        for paper in raw_papers
    ]


def build_evidence_chain(sources: tuple[Any, ...]) -> tuple[tuple[Evidence, ...], Report]:
    by_uri = {source.uri: source for source in sources}
    evidence = (
        Evidence(
            id="evidence_rag_grounding",
            source_id=by_uri["paper://rag-evaluation-survey"].id,
            quote=(
                "RAG evaluation should report retrieval quality and citation grounding."
            ),
            location="sentence 1",
        ),
        Evidence(
            id="evidence_citation_map",
            source_id=by_uri["paper://citation-mapping"].id,
            quote=(
                "Citation mapping connects every report claim to a quote, "
                "source URI, and paper title."
            ),
            location="sentence 1",
        ),
        Evidence(
            id="evidence_memory_policy",
            source_id=by_uri["paper://agent-memory-notes"].id,
            quote=(
                "Memory records can pollute an agent when write policy is missing."
            ),
            location="sentence 1",
        ),
        Evidence(
            id="evidence_delegation_budget",
            source_id=by_uri["paper://delegation-budgets"].id,
            quote=(
                "Child agents need isolated context and explicit budgets."
            ),
            location="sentence 1",
        ),
    )
    report = Report(
        id="report_capstone",
        run_id=RUN_ID,
        title="Capstone Cited Notes: Grounding, Memory, and Delegation",
        summary=(
            "Trustworthy local research assistants need citation grounding, "
            "memory write policy, and budgeted delegation."
        ),
        claims=(
            Claim(
                id="claim_grounding",
                text=(
                    "RAG evaluation should preserve citation grounding so readers "
                    "can audit generated claims."
                ),
                evidence_ids=["evidence_rag_grounding", "evidence_citation_map"],
            ),
            Claim(
                id="claim_memory",
                text=(
                    "Local research assistants should use write policies so memory "
                    "does not pollute later sessions."
                ),
                evidence_ids=["evidence_memory_policy"],
            ),
            Claim(
                id="claim_delegation",
                text=(
                    "Delegated review needs isolated child context and explicit budgets."
                ),
                evidence_ids=["evidence_delegation_budget"],
            ),
        ),
    )
    return evidence, report


def write_memory() -> tuple[MemoryEngine, tuple[MemoryRecord, ...]]:
    write_policy = MemoryWritePolicy(
        allowed_kinds=(MemoryKind.PINNED, MemoryKind.SEMANTIC, MemoryKind.EPISODIC),
        min_importance=0.4,
        max_content_chars=500,
        forbidden_phrases=("api key", "password"),
    )
    engine = MemoryEngine(write_policy=write_policy)
    engine.write(
        MemoryRecord(
            id="mem_citation_rule",
            kind=MemoryKind.PINNED,
            content="Always preserve citation links in research reports.",
            tags=("citation", "reporting", "capstone"),
            importance=0.95,
        )
    )
    engine.write(
        MemoryRecord(
            id="mem_rag_session",
            kind=MemoryKind.EPISODIC,
            content="Capstone session retrieved RAG evaluation and citation mapping papers.",
            tags=("rag", "session"),
            importance=0.7,
        )
    )
    recalled = engine.recall(
        MemoryRecallPolicy(query="citation reporting", allowed_kinds=tuple(MemoryKind), limit=3)
    )
    return engine, recalled


def load_skill() -> tuple[str, str]:
    runtime = SkillRuntime()
    package = runtime.load(SKILL_PATH)
    reference = runtime.read_reference(package, "references/citation-rules.md")
    return package.name, reference


def run_search_tool_trail(sources: tuple[Any, ...]) -> tuple[Any, list[str], str]:
    retriever = FakeRetriever(sources)

    def search_handler(arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments["query"])
        results = retriever.search(query, limit=3)
        return {
            "query": query,
            "hits": [
                {
                    "source_id": item.source_id,
                    "title": item.title,
                    "score": item.score,
                }
                for item in results
            ],
        }

    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="retriever.search",
            description="Search local paper fixtures.",
            handler=search_handler,
        )
    )
    tool_call_json = json.dumps(
        {
            "tool_call": {
                "id": "call_search_1",
                "name": "retriever.search",
                "arguments": {"query": "citation grounding"},
            }
        }
    )
    model = FakeModel(
        [
            FakeModelResponse(content=tool_call_json),
            FakeModelResponse(
                content=(
                    "Citation grounding matters: evaluation reports should keep "
                    "evidence links so claims stay auditable."
                )
            ),
        ]
    )
    result = AgentRunner(model=model, tools=tools, max_steps=4).run(
        run_id=RUN_ID,
        system_prompt="You are a local paper research assistant. Prefer cited claims.",
        user_message=RESEARCH_QUESTION,
    )
    return result.events, event_type_sequence(result.events), result.final_message.content


def run_delegation_review() -> tuple[str, tuple[Any, ...]]:
    role = AgentRolePolicy(
        id="role_reviewer",
        name="evidence-reviewer",
        system_prompt="Review claim-evidence links. Do not invent sources.",
        tool_names=("retriever.search",),
        skill_names=("citation-check",),  # declarative label unless factory wires SkillRuntime
        memory_kinds=("pinned", "semantic"),  # declarative label unless factory wires MemoryEngine
        max_steps=2,
    )

    def child_factory(child_role: AgentRolePolicy) -> AgentRunner:
        # Enforce tool allowlist explicitly (role fields alone do not filter tools).
        filter_tools_for_role(child_role, ("retriever.search",))
        tools = ToolRuntime()
        tools.register(
            ToolDefinition(
                name="retriever.search",
                description="Unused in this scripted child final answer.",
                handler=lambda arguments: {"ok": True},
            )
        )
        model = FakeModel(
            [
                FakeModelResponse(
                    content="Review complete: all three claims keep evidence IDs."
                )
            ]
        )
        return AgentRunner(model=model, tools=tools, max_steps=child_role.max_steps)

    task = DelegationTask(
        id="task_capstone_review",
        parent_run_id=RUN_ID,
        child_run_id=CHILD_RUN_ID,
        objective="Review Capstone claim-evidence links for unsupported claims.",
        role=role,
    )
    delegation = DelegationRuntime(child_runner_factory=child_factory)
    result = delegation.run_task(
        task,
        budget=DelegationBudget(max_child_runs=1, max_steps_per_child=2, max_total_steps=4),
    )
    if result.status is not DelegationStatus.COMPLETED:
        raise RuntimeError(f"delegation failed: {result.error_message}")
    return result.status.value, tuple(result.parent_events)


def build_snapshot(
    *,
    sources: tuple[Any, ...],
    evidence: tuple[Evidence, ...],
    report: Report,
    links: tuple[Any, ...],
    run_events: tuple[Any, ...],
    memory_records: tuple[MemoryRecord, ...],
    skill_name: str,
    delegation_status: str,
) -> WorkbenchSnapshot:
    project = WorkbenchProject(
        id=PROJECT_ID,
        title="Local Paper Research Assistant Capstone",
        description="Offline Capstone integrating Parts 1-7.",
    )
    run = WorkbenchRun(
        id=RUN_ID,
        project_id=PROJECT_ID,
        title="Capstone cited research run",
        question=RESEARCH_QUESTION,
        status=ResearchRunStatus.COMPLETED,
    )

    timeline_titles = {
        "model_request": "Model request",
        "model_response": "Model response",
        "tool_call": "Tool call",
        "tool_result": "Tool result",
        "delegate_start": "Delegate start",
        "delegate_finish": "Delegate finish",
        "error": "Error",
    }
    timeline = tuple(
        WorkbenchTimelineItem.from_event(
            event,
            title=timeline_titles.get(event.type.value, event.type.value),
            summary=f"{event.type.value} on {event.run_id}",
        )
        for event in run_events
        if event.run_id == RUN_ID
    )

    claim_ids_by_evidence_id: dict[str, tuple[str, ...]] = {}
    for claim in report.claims:
        for evidence_id in claim.evidence_ids:
            existing = claim_ids_by_evidence_id.get(evidence_id, ())
            claim_ids_by_evidence_id[evidence_id] = (*existing, claim.id)

    source_items = tuple(
        WorkbenchSourceItem.from_source(
            source,
            summary=f"Offline fixture {source.uri}",
            evidence=[item for item in evidence if item.source_id == source.id],
            claim_ids_by_evidence_id=claim_ids_by_evidence_id,
        )
        for source in sources
    )
    workbench_report = WorkbenchReport.from_report(report, claim_source_links=links)
    memory_items = tuple(
        WorkbenchMemoryItem.from_memory_record(
            record,
            title=record.id,
            summary=record.content[:80],
        )
        for record in memory_records
    )
    skills = (
        WorkbenchSkillItem(
            id="skill_citation_check",
            title="Citation check",
            name=skill_name,
            description="Progressive-disclosure citation checklist for Capstone reports.",
            status="loaded",
            resources=("references/citation-rules.md",),
        ),
    )
    delegation = (
        WorkbenchDelegationNode(
            id="task_capstone_review",
            title="Evidence review",
            role="evidence-reviewer",
            status=delegation_status,
            run_id=CHILD_RUN_ID,
            summary="Child reviewer confirmed claim-evidence IDs.",
            metadata={"parent_run_id": RUN_ID},
        ),
    )
    evals = (
        WorkbenchEvalItem(
            id="eval_claim_links",
            title="Claim source coverage",
            metric="claim_source_coverage",
            status="passed",
            score=1.0,
            details="All Capstone claims include source-backed evidence links.",
        ),
    )
    return WorkbenchSnapshot(
        project=project,
        run=run,
        timeline=timeline,
        delegation=delegation,
        sources=source_items,
        report=workbench_report,
        memory=memory_items,
        skills=skills,
        evals=evals,
    )


def production_boundary(
    events: tuple[Any, ...],
    store_path: Path,
) -> tuple[dict[str, Any], tuple[str, ...], str, str, bool]:
    diagnostics = RunDiagnostics.from_events(events)
    store = JsonlRunEventStore(store_path)
    if store_path.exists():
        store_path.unlink()
    store.append_many(events)
    approval = ApprovalPolicy(
        default_mode=ApprovalMode.REQUIRE_APPROVAL,
        default_reason="Unknown tool needs review.",
        rules=(
            ApprovalRule(
                tool_name_pattern="retriever.*",
                mode=ApprovalMode.ALLOW,
                reason="Read-only local retrieval is allowed.",
            ),
            ApprovalRule(
                tool_name_pattern="shell.*",
                mode=ApprovalMode.DENY,
                reason="Shell is blocked in Capstone.",
            ),
        ),
    )
    sandbox = SandboxPolicy(
        readable_paths=(CAPSTONE_ROOT,),
        writable_paths=(CAPSTONE_ROOT / "solution",),
        blocked_paths=(CAPSTONE_ROOT / "secrets",),
        allow_network=False,
        max_runtime_seconds=30,
    )
    return (
        diagnostics.to_record(),
        store.list_run_ids(),
        approval.decide("retriever.search").mode.value,
        approval.decide("shell.exec").mode.value,
        sandbox.network_decision().allowed,
    )


def run_capstone(*, trajectory_path: Path = TRAJECTORY_PATH) -> CapstoneResult:
    source_inputs = load_paper_inputs()
    sources = SourceIngestor().ingest_many(source_inputs)
    if len(sources) < 3:
        raise RuntimeError("Capstone requires at least 3 sources")

    # Retrieval is used both for the tool trail and for demonstrating ranking.
    top_hits = FakeRetriever(sources).search("citation grounding", limit=3)
    if not top_hits:
        raise RuntimeError("expected retrieval hits for citation grounding")

    evidence, report = build_evidence_chain(sources)
    links = build_claim_source_links(report, evidence=evidence, sources=sources)

    _engine, recalled = write_memory()
    skill_name, skill_reference = load_skill()
    if "unsupported claim" not in skill_reference.casefold():
        raise RuntimeError("skill reference should teach unsupported-claim rule")

    run_events, event_types, final_answer = run_search_tool_trail(sources)
    delegation_status, parent_events = run_delegation_review()

    # Parent timeline stays on RUN_ID; parent_events already use parent run id.
    combined_events = tuple(run_events) + tuple(parent_events)

    snapshot = build_snapshot(
        sources=sources,
        evidence=evidence,
        report=report,
        links=links,
        run_events=combined_events,
        memory_records=recalled,
        skill_name=skill_name,
        delegation_status=delegation_status,
    )
    diagnostics_record, jsonl_run_ids, approval_retrieval, approval_shell, network_allowed = (
        production_boundary(combined_events, trajectory_path)
    )

    return CapstoneResult(
        sources=sources,
        evidence=evidence,
        report=report,
        links=links,
        memory_records=recalled,
        skill_name=skill_name,
        skill_reference=skill_reference,
        run_events=combined_events,
        event_types=event_types,
        delegation_status=delegation_status,
        snapshot_record=snapshot.to_record(),
        diagnostics_record=diagnostics_record,
        jsonl_run_ids=jsonl_run_ids,
        approval_retrieval=approval_retrieval,
        approval_shell=approval_shell,
        network_allowed=network_allowed,
        final_answer=final_answer,
    )


def main() -> None:
    result = run_capstone()
    print("sources:", len(result.sources))
    print("evidence:", len(result.evidence))
    print("claims:", len(result.report.claims))
    print("links:", len(result.links))
    print("skill:", result.skill_name)
    print("memory_recalled:", [record.id for record in result.memory_records])
    print("event_types:", result.event_types)
    print("delegation:", result.delegation_status)
    print("timeline_items:", len(result.snapshot_record["timeline"]))
    print("diagnostics_events:", result.diagnostics_record["event_count"])
    print("jsonl_run_ids:", result.jsonl_run_ids)
    print("approval:", result.approval_retrieval, result.approval_shell)
    print("network_allowed:", result.network_allowed)
    print("final_answer:", result.final_answer)


if __name__ == "__main__":
    main()

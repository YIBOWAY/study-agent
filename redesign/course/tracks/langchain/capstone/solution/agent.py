"""LangChain track Capstone reference agent (offline, no research_core)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_course.agent_kernel import AgentStep
from langchain_course.delegation import (
    DelegationCoordinator,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    make_plain_agent_result,
    scripted_runner,
)
from langchain_course.memory import (
    MemoryKind,
    MemoryNote,
    MemoryWritePolicy,
    Notebook,
)
from langchain_course.production import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    JsonlStepStore,
    RunDiagnostics,
    SandboxPolicy,
)
from langchain_course.research import (
    ClaimItem,
    EvidenceItem,
    KeywordRetriever,
    PaperDoc,
    ResearchReport,
    build_claim_links,
)
from langchain_course.skills import SkillLoader
from langchain_course.workbench import (
    WorkbenchDelegationNode,
    WorkbenchEvalItem,
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReportPanel,
    WorkbenchRun,
    WorkbenchSkillItem,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
)

CAPSTONE_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = CAPSTONE_ROOT / "paper_fixtures" / "papers.json"
SKILL_PATH = CAPSTONE_ROOT / "skills" / "citation-check"

RESEARCH_QUESTION = (
    "Does citation grounding matter for trustworthy RAG evaluation, "
    "and what should a local research assistant remember or delegate "
    "when producing a cited report?"
)


@dataclass(slots=True)
class CapstoneResult:
    docs: list[PaperDoc]
    evidence: list[EvidenceItem]
    report: ResearchReport
    links: list[Any]
    memory_notes: list[MemoryNote]
    skill_name: str
    skill_reference_excerpt: str
    steps: list[AgentStep]
    snapshot: WorkbenchSnapshot
    diagnostics: RunDiagnostics
    approval_records: list[dict[str, str]]
    sandbox_records: list[dict[str, Any]]
    jsonl_path: Path
    delegation_summary: str


def load_paper_docs(path: Path = FIXTURES_PATH) -> list[PaperDoc]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    docs: list[PaperDoc] = []
    for index, item in enumerate(raw, start=1):
        docs.append(
            PaperDoc(
                id=f"paper_{index}",
                uri=str(item["uri"]),
                title=str(item["title"]),
                content=str(item["content"]),
            )
        )
    return docs


def build_evidence_and_report(
    docs: list[PaperDoc],
) -> tuple[list[EvidenceItem], ResearchReport]:
    retriever = KeywordRetriever(docs)
    hits = retriever.search("citation grounding RAG evaluation memory delegation", limit=4)
    if len(hits) < 3:
        # Fall back to first three docs if ranking is thin.
        chosen = docs[:3]
    else:
        by_id = {doc.id: doc for doc in docs}
        chosen = [by_id[hit.source_id] for hit in hits[:3]]

    evidence: list[EvidenceItem] = []
    claims: list[ClaimItem] = []
    for index, doc in enumerate(chosen, start=1):
        quote = doc.content.split(".")[0].strip() + "."
        evidence_id = f"evidence_{index}"
        claim_id = f"claim_{index}"
        evidence.append(
            EvidenceItem(
                id=evidence_id,
                source_id=doc.id,
                quote=quote,
                location="sentence 1",
            )
        )
        claims.append(
            ClaimItem(
                id=claim_id,
                text=quote,
                evidence_ids=[evidence_id],
            )
        )

    report = ResearchReport(
        id="report_lc_capstone",
        title="Citation Grounding for Local Research Assistants",
        summary=(
            "Citation grounding keeps RAG evaluation reports auditable. "
            "Local assistants should remember write policies and may delegate "
            "focused citation review under budgets."
        ),
        claims=claims,
    )
    return evidence, report


def run_capstone(*, jsonl_path: Path | None = None) -> CapstoneResult:
    docs = load_paper_docs()
    evidence, report = build_evidence_and_report(docs)
    links = build_claim_links(report, evidence=evidence, docs=docs)

    write_policy = MemoryWritePolicy(
        allowed_kinds=(MemoryKind.FACT, MemoryKind.WARNING, MemoryKind.PINNED),
        min_importance=2,
        banned_substrings=("password", "api_key"),
        max_content_len=500,
    )
    notebook = Notebook(write_policy=write_policy)
    note = notebook.write(
        MemoryNote(
            id="mem_cite_policy",
            kind=MemoryKind.FACT,
            content="Always attach evidence IDs to claims before accepting a report.",
            tags=("citation", "policy"),
            importance=5,
            pinned=True,
        )
    )

    skill_loader = SkillLoader()
    manifest = skill_loader.load(SKILL_PATH)
    rules = skill_loader.read_reference(manifest, "citation-rules.md")

    steps = [
        AgentStep(kind="model_request", payload={"step": "plan", "question": RESEARCH_QUESTION}),
        AgentStep(
            kind="tool_call",
            payload={"tool": "keyword_search", "query": "citation grounding"},
        ),
        AgentStep(
            kind="tool_result",
            payload={"tool": "keyword_search", "hit_count": len(docs)},
        ),
        AgentStep(kind="model_request", payload={"step": "synthesize"}),
        AgentStep(
            kind="final",
            payload={"text": report.summary},
        ),
    ]

    # Optional delegation: scripted child citation review.
    coord = DelegationCoordinator()
    role = WorkerRole(
        name="citation_reviewer",
        system_prompt="Check that every claim has evidence links.",
        max_steps=2,
        tool_names=(),
    )
    task = WorkerTask(
        task_id="t_cite_review",
        role=role,
        objective="Confirm claim_1..n have evidence_ids and links resolve.",
        context_messages=(
            report.summary,
            f"link_count={len(links)}",
        ),
    )
    budget = WorkerBudget(max_workers=1, max_steps_per_worker=2, max_total_steps=4)
    runner = scripted_runner(
        {"t_cite_review": make_plain_agent_result("all claims linked", model_requests=1)}
    )
    worker = coord.run_task(task, budget, runner=runner)
    steps.extend(list(coord.parent_steps))

    run_id = "run_lc_capstone"
    project = WorkbenchProject(
        id="project_lc_capstone",
        title="LangChain Capstone Research Assistant",
        description="Offline LC composition of Parts 1–7.",
        metadata={"track": "langchain"},
    )
    run = WorkbenchRun(
        id=run_id,
        project_id=project.id,
        title="Citation grounding Capstone run",
        question=RESEARCH_QUESTION,
        status="completed",
    )
    timeline = tuple(
        WorkbenchTimelineItem.from_step(step, run_id=run_id, index=index)
        for index, step in enumerate(steps)
    )
    sources = tuple(
        WorkbenchSourceItem.from_paper(doc, evidence=evidence) for doc in docs
    )
    snapshot = WorkbenchSnapshot(
        project=project,
        run=run,
        timeline=timeline,
        delegation=(
            WorkbenchDelegationNode(
                id="node_cite_review",
                title="Citation review",
                role=role.name,
                status=worker.status,
                run_id=run_id,
                summary=worker.final_text,
            ),
        ),
        sources=sources,
        report=WorkbenchReportPanel.from_report(report, links=links),
        memory=(WorkbenchMemoryItem.from_note(note),),
        skills=(WorkbenchSkillItem.from_manifest(manifest),),
        evals=(
            WorkbenchEvalItem(
                id="eval_has_links",
                metric="has_citation_links",
                passed=len(links) >= 3,
                score=1.0 if len(links) >= 3 else 0.0,
                detail=f"links={len(links)}",
            ),
        ),
    )

    diagnostics = RunDiagnostics.from_steps(run_id, steps)
    out_jsonl = jsonl_path or (Path(__file__).resolve().parent / "trajectory.jsonl")
    if out_jsonl.exists():
        out_jsonl.unlink()
    store = JsonlStepStore(out_jsonl)
    store.append_steps(run_id, steps)

    approval = ApprovalPolicy(
        rules=(
            ApprovalRule(
                tool_name_pattern="keyword_*",
                mode=ApprovalMode.ALLOW,
                reason="local keyword retrieval is allowed",
            ),
            ApprovalRule(
                tool_name_pattern="shell_*",
                mode=ApprovalMode.DENY,
                reason="shell tools are denied in Capstone sandbox",
            ),
        )
    )
    sandbox = SandboxPolicy(
        readable_paths=(CAPSTONE_ROOT,),
        writable_paths=(Path(__file__).resolve().parent,),
        allow_network=False,
        max_runtime_seconds=60,
    )
    approval_records = [
        approval.decide("keyword_search").to_record(),
        approval.decide("shell_rm").to_record(),
    ]
    sandbox_records = [
        sandbox.network_decision().to_record(),
        sandbox.decide_path(FIXTURES_PATH, access="read").to_record(),
    ]

    return CapstoneResult(
        docs=docs,
        evidence=evidence,
        report=report,
        links=links,
        memory_notes=[note],
        skill_name=manifest.name,
        skill_reference_excerpt=rules[:120],
        steps=steps,
        snapshot=snapshot,
        diagnostics=diagnostics,
        approval_records=approval_records,
        sandbox_records=sandbox_records,
        jsonl_path=out_jsonl,
        delegation_summary=worker.final_text,
    )


if __name__ == "__main__":
    result = run_capstone()
    record = result.snapshot.to_record()
    print("sources:", len(result.docs))
    print("evidence:", len(result.evidence))
    print("links:", len(result.links))
    print("timeline:", len(record["timeline"]))
    print("diagnostics events:", result.diagnostics.event_count)
    print("jsonl:", result.jsonl_path)

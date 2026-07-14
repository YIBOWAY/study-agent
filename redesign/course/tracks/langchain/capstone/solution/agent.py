"""LangChain track Capstone reference agent (offline, no research_core)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool, StructuredTool
from langchain_course.agent_kernel import AgentRunResult, AgentStep, run_tool_calling_agent
from langchain_course.delegation import (
    DelegationCoordinator,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    compile_child_prompt,
)
from langchain_course.fake_models import (
    DeterministicToolCallingChatModel,
    tool_then_final_model,
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
    LangChainTraceRecorder,
    RunDiagnostics,
    SandboxPolicy,
    build_approval_hook,
)
from langchain_course.research import (
    ClaimItem,
    EvidenceItem,
    LangChainPaperRetriever,
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
    callback_records: list[dict[str, Any]]


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
    retriever = LangChainPaperRetriever.from_papers(docs, k=4)
    documents = retriever.invoke(
        "citation grounding RAG evaluation memory delegation"
    )
    if len(documents) < 3:
        # Fall back to first three docs if ranking is thin.
        chosen = docs[:3]
    else:
        by_id = {doc.id: doc for doc in docs}
        chosen = [
            by_id[str(document.metadata["source_id"])]
            for document in documents[:3]
        ]

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


def build_keyword_search_tool(docs: list[PaperDoc]) -> BaseTool:
    retriever = LangChainPaperRetriever.from_papers(docs, k=3)

    def keyword_search(query: str) -> str:
        """Search local paper fixtures and return stable source ids."""
        documents = retriever.invoke(query)
        return json.dumps(
            [
                {
                    "source_id": document.metadata["source_id"],
                    "source_uri": document.metadata["source_uri"],
                    "snippet": document.page_content[:160],
                }
                for document in documents
            ],
            ensure_ascii=False,
        )

    return StructuredTool.from_function(keyword_search, name="keyword_search")


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
    search_tool = build_keyword_search_tool(docs)
    model = tool_then_final_model(
        tool_name="keyword_search",
        tool_args={"query": "citation grounding"},
        final_text=report.summary,
        call_id="capstone_search_1",
    )
    callback_recorder = LangChainTraceRecorder()
    agent_result = run_tool_calling_agent(
        user_message=RESEARCH_QUESTION,
        system_prompt=(
            "Use the local keyword_search tool before answering. "
            "Keep claims tied to inspectable evidence."
        ),
        tools=[search_tool],
        model=model,
        config={"callbacks": [callback_recorder], "tags": ["lc-capstone"]},
        before_tool=build_approval_hook(approval),
    )
    steps = list(agent_result.steps)

    # Optional delegation: deterministic child through the real LC model loop.
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
    child_model = DeterministicToolCallingChatModel(
        responses=[AIMessage(content="all claims linked")]
    )

    def runner(worker_task: WorkerTask, tools: list[BaseTool]) -> AgentRunResult:
        return run_tool_calling_agent(
            user_message=compile_child_prompt(worker_task),
            system_prompt=worker_task.role.system_prompt,
            tools=tools,
            model=child_model,
            max_steps=worker_task.role.max_steps,
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
        callback_records=list(callback_recorder.records),
    )


def run_live_capstone_agent() -> AgentRunResult:
    """Optional DeepSeek smoke using the same local tool and approval boundary."""
    docs = load_paper_docs()
    search_tool = build_keyword_search_tool(docs)
    policy = ApprovalPolicy(
        rules=(
            ApprovalRule(
                tool_name_pattern="keyword_*",
                mode=ApprovalMode.ALLOW,
                reason="local fixture retrieval",
            ),
        )
    )
    return run_tool_calling_agent(
        user_message=(
            f"{RESEARCH_QUESTION} You must call keyword_search once before answering."
        ),
        tools=[search_tool],
        before_tool=build_approval_hook(policy),
        max_steps=4,
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

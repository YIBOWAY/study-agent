from __future__ import annotations

import pytest
from langchain_course.agent_kernel import AgentStep
from langchain_course.memory import MemoryKind, MemoryNote
from langchain_course.research import ClaimLink, EvidenceItem, PaperDoc, ResearchReport
from langchain_course.workbench import (
    WorkbenchError,
    WorkbenchEvalItem,
    WorkbenchMemoryItem,
    WorkbenchProject,
    WorkbenchReportPanel,
    WorkbenchRun,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
    build_demo_snapshot,
)


def test_timeline_from_step_and_demo_record_keys() -> None:
    step = AgentStep(kind="tool_call", payload={"tool": "echo"})
    item = WorkbenchTimelineItem.from_step(step, run_id="run_1", index=0)
    assert item.type == "tool_call"
    assert item.id == "run_1_step_0"
    demo = build_demo_snapshot()
    record = demo.to_record()
    assert set(record.keys()) == {
        "project",
        "run",
        "timeline",
        "delegation",
        "sources",
        "report",
        "memory",
        "skills",
        "evals",
    }
    assert record["run"]["project_id"] == record["project"]["id"]
    assert len(record["timeline"]) == 3
    assert record["report"]["links"][0]["source_id"] == "paper_1"


def test_snapshot_rejects_mismatched_run_project() -> None:
    project = WorkbenchProject(id="p1", title="P")
    run = WorkbenchRun(
        id="r1",
        project_id="other",
        title="R",
        question="Q",
    )
    with pytest.raises(WorkbenchError, match="project_id"):
        WorkbenchSnapshot(project=project, run=run)


def test_snapshot_rejects_unknown_report_source() -> None:
    project = WorkbenchProject(id="p1", title="P")
    run = WorkbenchRun(id="r1", project_id="p1", title="R", question="Q")
    report = WorkbenchReportPanel(
        id="rep",
        title="t",
        summary="s",
        links=(
            {
                "claim_id": "c1",
                "evidence_id": "e1",
                "source_id": "missing_paper",
                "source_uri": "x",
                "source_title": "y",
                "quote": "z",
            },
        ),
    )
    with pytest.raises(WorkbenchError, match="unknown source_id"):
        WorkbenchSnapshot(project=project, run=run, report=report)


def test_adapters_from_domain_objects() -> None:
    doc = PaperDoc(id="paper_1", uri="paper://x", title="T", content="body")
    evidence = [EvidenceItem(id="e1", source_id="paper_1", quote="body")]
    source = WorkbenchSourceItem.from_paper(doc, evidence=evidence)
    assert source.evidence_ids == ("e1",)
    note = MemoryNote(
        id="m1",
        kind=MemoryKind.FACT,
        content="Always cite sources.",
        pinned=True,
        tags=("policy",),
    )
    mem = WorkbenchMemoryItem.from_note(note)
    assert mem.to_record()["pinned"] is True
    report = ResearchReport(id="r1", title="t", summary="s")
    link = ClaimLink(
        claim_id="c1",
        evidence_id="e1",
        source_id="paper_1",
        source_uri=doc.uri,
        source_title=doc.title,
        quote="body",
    )
    panel = WorkbenchReportPanel.from_report(report, links=[link])
    assert panel.to_record()["links"][0]["quote"] == "body"
    eval_item = WorkbenchEvalItem(id="e", metric="has_citation", passed=True, score=1.0)
    assert eval_item.to_record()["score"] == 1.0


def test_eval_score_bounds() -> None:
    with pytest.raises(WorkbenchError, match="between 0 and 1"):
        WorkbenchEvalItem(id="e", metric="m", passed=False, score=1.5)

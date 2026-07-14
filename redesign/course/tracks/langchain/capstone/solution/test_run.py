"""Offline rubric-backed tests for the LC Capstone reference solution."""

from __future__ import annotations

from pathlib import Path

from agent import run_capstone
from langchain_course.production import JsonlStepStore
from langchain_course.research import build_claim_links


def test_capstone_rubric_core_invariants(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "trajectory.jsonl"
    result = run_capstone(jsonl_path=jsonl_path)

    # 1. sources + evidence
    assert len(result.docs) >= 3
    assert len(result.evidence) >= 3
    source_ids = {doc.id for doc in result.docs}
    for item in result.evidence:
        assert item.source_id in source_ids

    # 2. claims link to evidence
    assert result.report.claims
    for claim in result.report.claims:
        assert claim.evidence_ids
    links = build_claim_links(
        result.report, evidence=result.evidence, docs=result.docs
    )
    assert len(links) >= 3
    assert links[0].source_uri.startswith("paper://")

    # 3. skill + memory
    assert result.skill_name == "citation-check"
    excerpt = result.skill_reference_excerpt.lower()
    assert "quote" in excerpt or "claim" in excerpt
    assert len(result.memory_notes) >= 1
    assert result.memory_notes[0].content

    # 4. workbench timeline
    record = result.snapshot.to_record()
    assert set(record.keys()) >= {
        "project",
        "run",
        "timeline",
        "sources",
        "report",
        "memory",
        "skills",
    }
    assert record["timeline"]
    assert record["run"]["id"] == "run_lc_capstone"
    assert all(item["run_id"] == "run_lc_capstone" for item in record["timeline"])
    assert record["report"] is not None
    assert len(record["sources"]) >= 3

    # 5. production trust evidence
    assert result.diagnostics.event_count == len(result.steps)
    store = JsonlStepStore(jsonl_path)
    replay = store.read_run("run_lc_capstone")
    assert len(replay) == len(result.steps)
    assert result.approval_records[0]["mode"] == "allow"
    assert result.approval_records[1]["mode"] == "deny"
    assert result.sandbox_records[0]["subject"] == "network"
    assert result.sandbox_records[0]["allowed"] is False

    # bonus: delegation trail present
    kinds = [step.kind for step in result.steps]
    assert "delegate_start" in kinds
    assert "delegate_finish" in kinds
    assert result.delegation_summary


def test_capstone_snapshot_eval_passed(tmp_path: Path) -> None:
    result = run_capstone(jsonl_path=tmp_path / "t.jsonl")
    evals = result.snapshot.to_record()["evals"]
    assert evals
    assert evals[0]["passed"] is True

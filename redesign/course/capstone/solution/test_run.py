"""Rubric-backed tests for the Capstone reference solution."""

from __future__ import annotations

from pathlib import Path

from agent import RUN_ID, run_capstone
from research_core.research import build_claim_source_links

SOLUTION_DIR = Path(__file__).resolve().parent



def test_capstone_meets_six_success_criteria(tmp_path) -> None:
    trajectory = tmp_path / "trajectory.jsonl"
    result = run_capstone(trajectory_path=trajectory)

    # 1. Evidence from at least 3 sources
    assert len(result.sources) >= 3
    source_ids = {source.id for source in result.sources}
    evidence_source_ids = {item.source_id for item in result.evidence}
    assert len(result.evidence) >= 3
    assert evidence_source_ids <= source_ids
    assert len(evidence_source_ids) >= 3

    # 2. Every claim traces to evidence
    assert result.report.claims
    for claim in result.report.claims:
        assert claim.evidence_ids
    links = build_claim_source_links(
        result.report,
        evidence=result.evidence,
        sources=result.sources,
    )
    assert len(links) >= len(result.report.claims)
    assert {link.source_uri for link in links}
    assert all(link.quote for link in links)

    # 3. At least 1 skill and 1 memory policy usage
    assert result.skill_name == "citation-check"
    assert "unsupported claim" in result.skill_reference.casefold()
    assert result.memory_records
    assert any(record.id == "mem_citation_rule" for record in result.memory_records)

    # 4. Workbench timeline inspectable
    record = result.snapshot_record
    assert sorted(record.keys()) == [
        "delegation",
        "evals",
        "memory",
        "project",
        "report",
        "run",
        "skills",
        "sources",
        "timeline",
    ]
    assert record["run"]["id"] == RUN_ID
    assert record["timeline"]
    assert all(item["run_id"] == RUN_ID for item in record["timeline"])
    assert record["report"] is not None
    assert record["report"]["claim_source_links"]

    # 5. Offline production trust evidence (bonus but asserted in solution)
    assert result.diagnostics_record["run_id"] == RUN_ID
    assert result.diagnostics_record["event_count"] >= 4
    assert RUN_ID in result.jsonl_run_ids
    assert trajectory.exists()
    assert result.approval_retrieval == "allow"
    assert result.approval_shell == "deny"
    assert result.network_allowed is False

    # Event trail includes tool use from Part 1 composition
    assert "tool_call" in result.event_types
    assert "tool_result" in result.event_types
    assert result.delegation_status == "completed"
    assert result.final_answer


def test_solution_artifacts_exist() -> None:
    assert (SOLUTION_DIR / "report.md").is_file()
    assert (SOLUTION_DIR / "reflection.md").is_file()
    assert (SOLUTION_DIR / "agent.py").is_file()

"""Starter scaffold tests — skip until TODOs are implemented."""

from __future__ import annotations

from pathlib import Path

import pytest
from agent_starter import run_capstone


def test_starter_run_capstone(tmp_path: Path) -> None:
    try:
        result = run_capstone(jsonl_path=tmp_path / "trajectory.jsonl")
    except NotImplementedError:
        pytest.skip("starter TODOs not implemented yet")

    assert len(result.docs) >= 3
    assert len(result.evidence) >= 3
    assert result.report.claims
    assert result.links
    assert result.memory_notes
    assert result.skill_name
    record = result.snapshot.to_record()
    assert record["timeline"]
    assert result.diagnostics.event_count >= 1

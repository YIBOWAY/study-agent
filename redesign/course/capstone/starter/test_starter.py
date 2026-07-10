"""Starter tests.

These tests document the Capstone target shape. They skip until you remove
NotImplementedError from agent_starter.py and implement the TODOs.
"""

from __future__ import annotations

import pytest
from agent_starter import run_starter


def test_starter_capstone_shape(tmp_path) -> None:
    try:
        result = run_starter(tmp_trajectory=tmp_path / "events.jsonl")
    except NotImplementedError as exc:
        pytest.skip(f"starter incomplete: {exc}")

    assert len(result["sources"]) >= 3
    assert len(result["evidence"]) >= 3
    assert result["report"].claims
    assert all(claim.evidence_ids for claim in result["report"].claims)
    assert result["links"]
    assert result["memory_records"]
    assert result["skill_name"]
    assert result["snapshot_record"]["timeline"]
    assert "tool_call" in result["event_types"] or result["event_types"]
    assert result["production"]

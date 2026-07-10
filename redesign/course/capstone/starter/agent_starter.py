"""Capstone starter skeleton.

Fill every TODO. Keep the assistant offline: paper fixtures + FakeModel/FakeRetriever only.
Run from redesign/:

    PYTHONPATH=packages/research_core/src uv run pytest course/capstone/starter/test_starter.py -q
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_core.memory import (
    MemoryEngine,
    MemoryKind,
    MemoryRecord,
    MemoryWritePolicy,
)
from research_core.product import (
    WorkbenchProject,
    WorkbenchRun,
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
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime, event_type_sequence
from research_core.skills import SkillRuntime
from research_core.testing import FakeModel, FakeModelResponse

CAPSTONE_ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = CAPSTONE_ROOT / "paper_fixtures" / "papers.json"
SKILL_PATH = CAPSTONE_ROOT / "skills" / "citation-check"

RUN_ID = "run_capstone_starter"
PROJECT_ID = "project_capstone_starter"
RESEARCH_QUESTION = (
    "Does citation grounding matter for trustworthy RAG evaluation?"
)


def load_sources() -> tuple[Any, ...]:
    """TODO: load papers.json and ingest with SourceIngestor."""
    raw = json.loads(PAPERS_PATH.read_text(encoding="utf-8"))
    inputs = [
        SourceInput(uri=paper["uri"], title=paper["title"], content=paper["content"])
        for paper in raw
    ]
    if not inputs:
        raise ValueError("papers.json produced no SourceInput rows")
    # TODO: return SourceIngestor().ingest_many(inputs)
    raise NotImplementedError(
        f"load_sources: ingest {len(inputs)} fixtures with SourceIngestor"
    )


def build_report(sources: tuple[Any, ...]) -> tuple[tuple[Evidence, ...], Report]:
    """TODO: create >=3 evidence items and a report whose claims all have evidence_ids."""
    raise NotImplementedError("build_report: create evidence + claims + report")


def use_memory_and_skill() -> tuple[tuple[MemoryRecord, ...], str]:
    """TODO: write memory under MemoryWritePolicy and load citation-check skill."""
    raise NotImplementedError("use_memory_and_skill: MemoryEngine + SkillRuntime")


def run_tool_trail(sources: tuple[Any, ...]) -> tuple[tuple[Any, ...], list[str]]:
    """TODO: script FakeModel tool_call for retriever.search and return events."""
    raise NotImplementedError("run_tool_trail: AgentRunner + FakeModel + ToolRuntime")


def build_workbench(
    *,
    sources: tuple[Any, ...],
    evidence: tuple[Evidence, ...],
    report: Report,
    events: tuple[Any, ...],
) -> dict[str, Any]:
    """TODO: assemble WorkbenchSnapshot and return to_record()."""
    raise NotImplementedError("build_workbench: WorkbenchSnapshot.to_record()")


def production_checks(events: tuple[Any, ...], path: Path) -> dict[str, Any]:
    """TODO: diagnostics + JSONL store + approval/sandbox decisions."""
    raise NotImplementedError("production_checks: Part 7 contracts")


def run_starter(tmp_trajectory: Path | None = None) -> dict[str, Any]:
    """Compose Capstone pieces. Replace NotImplementedError TODOs above."""
    sources = load_sources()
    evidence, report = build_report(sources)
    links = build_claim_source_links(report, evidence=evidence, sources=sources)
    memory_records, skill_name = use_memory_and_skill()
    events, event_types = run_tool_trail(sources)
    snapshot_record = build_workbench(
        sources=sources,
        evidence=evidence,
        report=report,
        events=events,
    )
    trajectory = tmp_trajectory or (Path.cwd() / "capstone-starter-events.jsonl")
    production = production_checks(events, trajectory)
    return {
        "sources": sources,
        "evidence": evidence,
        "report": report,
        "links": links,
        "memory_records": memory_records,
        "skill_name": skill_name,
        "events": events,
        "event_types": event_types,
        "snapshot_record": snapshot_record,
        "production": production,
    }


# --- Optional reference fragments (read-only hints; prefer writing your own) ---

def _hint_tool_call_json() -> str:
    return json.dumps(
        {
            "tool_call": {
                "id": "call_1",
                "name": "retriever.search",
                "arguments": {"query": "citation grounding"},
            }
        }
    )


# Silence unused-import linters while starter is incomplete.
_STARTER_IMPORT_ANCHORS = (
    MemoryEngine,
    MemoryKind,
    MemoryWritePolicy,
    WorkbenchProject,
    WorkbenchRun,
    WorkbenchSnapshot,
    WorkbenchSourceItem,
    WorkbenchTimelineItem,
    ApprovalMode,
    ApprovalPolicy,
    ApprovalRule,
    JsonlRunEventStore,
    RunDiagnostics,
    SandboxPolicy,
    Claim,
    SourceIngestor,
    FakeRetriever,
    ResearchRunStatus,
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
    SkillRuntime,
    FakeModel,
    FakeModelResponse,
    _hint_tool_call_json,
)

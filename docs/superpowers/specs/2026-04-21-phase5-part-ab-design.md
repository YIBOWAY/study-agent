# Phase 5 Part A+B Design

**Date:** 2026-04-21

## Goal

Extend the Phase 4 research assistant with:

1. A teaching-grade memory system with short-term session memory, long-term persisted insights, and working-memory fields in research state.
2. A new `agent_v2` LangGraph flow that adds memory recall, planning, reflection, and one-pass report revision.

This work must preserve the existing `workflow` and `agent` modes and keep all current tests passing.

## Constraints

- Keep all LLM calls inside `LLMService` using `httpx`.
- Do not modify `app/services/research/workflow.py` or `app/services/research/agent.py`.
- Do not modify existing Phase 4 test files; add new Phase 5 test files instead.
- Do not add new external dependencies.
- Use `from __future__ import annotations` in new files.

## Architecture

### Memory Layer

Add `app/services/memory_service.py` as an isolated service with no FastAPI or LangGraph knowledge.

- Short-term memory:
  - in-process `dict[str, SessionMemory]`
  - session-scoped
  - TTL enforced on read
- Long-term memory:
  - persisted JSON file under `data/memory/long_term.json`
  - loaded at service startup
  - bounded by `memory_max_insights`
- Concurrency:
  - `asyncio.Lock` protects file reads/writes
  - file IO runs via `asyncio.to_thread`

### Research State Extension

Extend `ResearchState` with `NotRequired` fields:

- `plan: list[str]`
- `current_step: str`
- `reflection: str`
- `session_id: str`
- `prior_insights: list[str]`

Using `NotRequired` keeps old Phase 4 initial states valid so `workflow.py` and `agent.py` do not need changes.

### New Research Nodes

Append new node factories to `app/services/research/nodes.py`:

- `make_recall_memory_node`
- `make_plan_node`
- `make_reflect_node`
- `make_revise_report_node`
- `make_save_memory_node`

Existing node factories remain available. Existing behavior stays compatible. Optional context from `plan`, `current_step`, and `prior_insights` may be incorporated by reading with `state.get(...)`.

### New Graph

Add `app/services/research/agent_v2.py` with this structure:

`START -> recall_memory -> plan -> rewrite_query -> search -> evaluate_results`

- `sufficient -> generate_report -> reflect`
- `reflect pass -> save_memory -> END`
- `reflect revise -> revise_report -> save_memory -> END`
- `needs_more -> refine_query -> search -> ...`

The revision loop is structurally capped at one revision by routing `revise_report` directly to `save_memory`, not back into `reflect`.

### API Layer

Update `ResearchRequest` / `ResearchResponse` and `POST /api/v1/research` to support:

- `workflow`
- `agent`
- `agent_v2`

Add a new memory management router:

- `GET /api/v1/memory/insights`
- `GET /api/v1/memory/insights/search`
- `GET /api/v1/memory/sessions/{session_id}`
- `DELETE /api/v1/memory/sessions/{session_id}`
- `DELETE /api/v1/memory/insights`

## Key Behavioral Decisions

### Reflection Audit Trail

`reflect` stores the real reviewer output in `reflection`. `revise_report` does not overwrite it with `"pass"`. This preserves the feedback for debugging and response payloads. The single-revision limit is enforced by graph topology instead of state mutation.

### Sessionless Operation

When `session_id == ""`, memory recall and save nodes do not error. They write trace steps that memory was skipped and continue.

### Insight Retrieval

Long-term memory retrieval uses keyword-overlap scoring only. This is intentionally simple and deterministic for the learning project.

## Files

### New Files

- `app/services/memory_service.py`
- `app/services/research/agent_v2.py`
- `app/api/routes/memory.py`
- `tests/test_memory_service.py`
- `tests/test_research_nodes_phase5.py`
- `tests/test_research_agent_v2.py`
- `tests/test_research_endpoint_phase5.py`
- `tests/test_memory_endpoint.py`

### Modified Files

- `app/core/config.py`
- `app/services/research/state.py`
- `app/services/research/nodes.py`
- `app/services/research/__init__.py`
- `app/schemas/research.py`
- `app/api/routes/research.py`
- `app/main.py`
- `.gitignore`

## Test Strategy

1. Add dedicated tests for `MemoryService`.
2. Add new Phase 5 node tests in a separate file so existing node tests remain untouched.
3. Add a focused integration suite for `agent_v2`.
4. Add route tests for `agent_v2` and memory endpoints.
5. Run full `pytest -q` to prove backward compatibility.

## Risks

- Extending `ResearchState` may interact badly with LangGraph state handling.
  - Mitigation: use `NotRequired` fields and `state.get(...)` access.
- Memory persistence may leak state across tests.
  - Mitigation: use `tmp_path` and patch route-level memory service in tests.
- Prompt JSON parsing may fail.
  - Mitigation: add deterministic fallbacks for all new LLM-backed nodes.

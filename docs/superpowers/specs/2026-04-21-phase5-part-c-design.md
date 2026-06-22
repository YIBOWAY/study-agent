# Phase 5 Part C Design

**Date:** 2026-04-21

## Goal

Add a teaching-grade multi-agent research mode that demonstrates role-based collaboration while reusing the existing Phase 4 and Phase 5 single-agent foundations.

The new mode must:

- preserve existing `workflow`, `agent`, and `agent_v2` behavior
- expose a new `mode="multi_agent"` API path
- reuse the existing `MemoryService` lightly at graph entry and exit
- remain deterministic and testable without introducing a separate LLM-driven supervisor node

## Core Architecture

### New Module Boundary

Create a dedicated `app/services/multi_agent/` package:

- `state.py` defines `MultiAgentState`
- `roles.py` defines role node factories and route helpers
- `graph.py` builds and runs the LangGraph flow
- `__init__.py` exports `run_multi_agent`

This keeps multi-agent concerns separate from the existing `research/` package and avoids mixing single-agent and multi-agent orchestration in the same files.

### Memory Strategy

Memory is integrated at the supervisor level, not per-role.

- graph entry: call the existing `make_recall_memory_node`
- graph exit: call the existing `make_save_memory_node`
- intermediate role nodes consume `prior_insights` from shared state only

This preserves a single memory contract across `agent_v2` and `multi_agent` while keeping roles simple and testable.

### Supervisor Model

There is no separate LLM supervisor node.

The supervisor behavior is expressed by graph topology and conditional routing:

- analysis decides whether more research is needed
- review decides whether one revision is needed
- explicit routing helpers enforce termination conditions

This is intentionally less flashy than a “real” autonomous supervisor, but it is far more stable for a learning project and much easier to verify with pytest.

## State Design

`MultiAgentState` reuses `ResearchSearchResult` and `ResearchStep` from `research/state.py`.

Fields:

- shared:
  - `topic`
  - `queries`
  - `search_results`
  - `report`
  - `steps`
- graph control:
  - `plan`
  - `current_step`
  - `current_phase`
  - `iteration`
  - `max_iterations`
  - `top_k`
- analyst outputs:
  - `analysis`
  - `evaluation`
- reviewer outputs:
  - `review_verdict`
  - `review_feedback`
  - `revision_count`
- memory:
  - `session_id`
  - `prior_insights`

`queries` is intentionally retained so the public research response stays structurally consistent with existing modes and existing query-refinement helpers remain reusable.

## Graph Design

The graph structure is:

`START -> recall_memory -> plan_research -> researcher -> analyst`

Then:

- `analysis sufficient -> writer -> reviewer`
- `analysis needs_more -> refine_query -> researcher -> analyst`

After review:

- `approved -> save_memory -> END`
- `needs_revision and revision_count == 0 -> writer -> reviewer`
- `needs_revision and revision_count >= 1 -> save_memory -> END`

Termination safeguards:

- if `iteration >= max_iterations`, route to `writer` even if analysis still says `needs_more`
- if `revision_count >= 1`, do not allow a second revision loop

## Role Responsibilities

### plan_research

Reuse or lightly wrap the existing planning node so the multi-agent mode starts with the same task-decomposition semantics as `agent_v2`.

### researcher

Acts as the search specialist.

- generates or refines the next query
- executes multi-source search using the existing research search logic
- updates `queries`, `search_results`, `iteration`, and `current_step`

This is implemented as a role wrapper that reuses existing rewrite/refine/search behavior rather than duplicating retrieval code.

### analyst

Transforms evidence into:

- structured `analysis`
- `evaluation = sufficient | needs_more`

The analyst prompt focuses on evidence synthesis and sufficiency judgment, not final report writing.

### writer

Produces either:

- an initial report when there is no review feedback
- a revised report when `review_feedback` is present

This avoids adding a separate revision node in the multi-agent flow.

### reviewer

Evaluates the report and returns:

- `review_verdict = approved | needs_revision`
- `review_feedback`

The review loop is bounded to one revision.

## API Integration

### Research schema

Extend:

- `ResearchRequest.mode` to include `multi_agent`
- `ResearchResponse` with:
  - `analysis`
  - `review_verdict`
  - `agents_involved`

These fields default to empty values so old modes remain valid.

### Research route

Add a `multi_agent` branch that calls `run_multi_agent`.

The route reuses the existing module-level `memory_service`. `session_id` remains optional; when empty, memory is skipped gracefully.

## Test Strategy

### Unit tests

- `tests/test_multi_agent_roles.py`
  - researcher
  - analyst
  - writer
  - reviewer

### Integration tests

- `tests/test_multi_agent_graph.py`
  - happy path
  - needs more research
  - one revision path
  - max iteration exit
  - no-memory path
  - memory-enabled path

### API tests

- extend `tests/test_research_endpoint_phase5.py`
  - `mode="multi_agent"`
  - `session_id` propagation

### Final verification

- targeted Part C suite
- full `pytest -q`

## Risks and Mitigations

- Risk: duplicated logic between `research/` and `multi_agent/`
  - Mitigation: wrap and reuse existing node behavior where practical instead of copying helpers.

- Risk: role prompts become too broad and collapse back into a single-agent design
  - Mitigation: keep each role prompt narrow and role-specific.

- Risk: multi-agent loops become non-terminating
  - Mitigation: preserve explicit iteration and revision caps in routing helpers.

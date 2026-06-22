# Phase 5 Part C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `multi_agent` research mode that demonstrates planner/researcher/analyst/writer/reviewer collaboration on top of the existing memory-enabled research system.

**Architecture:** Implement multi-agent orchestration in a dedicated `app/services/multi_agent/` package. Reuse memory only at graph entry and exit, reuse existing research planning/query/search helpers where practical, and express supervisor logic as graph routing instead of a separate LLM node.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, LangGraph, pytest, asyncio

---

### Task 1: Add Part C Documentation Scaffold

**Files:**
- Create: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\specs\2026-04-21-phase5-part-c-design.md`
- Create: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\plans\2026-04-21-phase5-part-c.md`
- Create: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\logs\2026-04-21-phase5-part-c-progress.md`

- [ ] **Step 1: Record design, implementation plan, and progress log**

Write the approved design, execution plan, and a running implementation log under `docs/superpowers`.

### Task 2: Define Multi-Agent State and Red Tests

**Files:**
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\multi_agent\state.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_multi_agent_roles.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_multi_agent_graph.py`

- [ ] **Step 1: Write the failing tests**

Add unit tests for role nodes and integration tests for the graph:
- happy path
- additional research loop
- one revision loop
- max-iteration exit
- memory/no-memory variants

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_multi_agent_roles.py tests/test_multi_agent_graph.py`
Expected: FAIL because the multi-agent package does not exist yet.

### Task 3: Implement Multi-Agent Roles and Graph

**Files:**
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\multi_agent\roles.py`
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\multi_agent\graph.py`
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\multi_agent\__init__.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\logs\2026-04-21-phase5-part-c-progress.md`

- [ ] **Step 1: Write minimal implementation**

Implement:
- `MultiAgentState`
- role factories for `researcher`, `analyst`, `writer`, `reviewer`
- planning/recall/save wrappers
- graph routing helpers
- `run_multi_agent`

- [ ] **Step 2: Run role and graph tests**

Run: `conda run -n ai-agent pytest -q tests/test_multi_agent_roles.py tests/test_multi_agent_graph.py`
Expected: PASS

### Task 4: Integrate `multi_agent` into Research API

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\schemas\research.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\api\routes\research.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\tests\test_research_endpoint_phase5.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\logs\2026-04-21-phase5-part-c-progress.md`

- [ ] **Step 1: Write the failing endpoint tests**

Extend the Phase 5 endpoint suite with:
- `mode="multi_agent"`
- `session_id` propagation
- response fields `analysis`, `review_verdict`, `agents_involved`

- [ ] **Step 2: Run endpoint test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_research_endpoint_phase5.py`
Expected: FAIL because the API does not yet recognize `multi_agent`.

- [ ] **Step 3: Implement route and schema updates**

Add `multi_agent` to request/response schema and route dispatch.

- [ ] **Step 4: Run endpoint tests to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_research_endpoint_phase5.py`
Expected: PASS

### Task 5: Final Verification

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\docs\superpowers\logs\2026-04-21-phase5-part-c-progress.md`

- [ ] **Step 1: Run targeted Part C tests**

Run: `conda run -n ai-agent pytest -q tests/test_multi_agent_roles.py tests/test_multi_agent_graph.py tests/test_research_endpoint_phase5.py`
Expected: PASS

- [ ] **Step 2: Run full regression suite**

Run: `conda run -n ai-agent pytest -q`
Expected: PASS with all earlier phases still green.

# Phase 5 Part A+B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add memory, planning, and reflection to the research assistant via a new `agent_v2` path while preserving all existing Phase 4 behavior.

**Architecture:** Introduce a standalone `MemoryService`, extend `ResearchState` with optional working-memory fields, append new research node factories, and add a separate `agent_v2` graph instead of refactoring the old graphs. Route-level integration exposes the new behavior through `mode="agent_v2"` and dedicated memory endpoints.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, LangGraph, pytest, asyncio, json

---

### Task 1: Add Memory Configuration and Service

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\core\config.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\.gitignore`
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\memory_service.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_memory_service.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:
- insight save/retrieve
- no-match retrieval
- session add/get/clear
- JSON persistence across instances
- max insight trimming

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_memory_service.py`
Expected: FAIL because `MemoryService` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement:
- `InsightRecord` and `SessionMemory` typed dicts
- JSON-backed long-term memory with `asyncio.Lock`
- short-term memory with TTL cleanup on read
- keyword-overlap retrieval

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_memory_service.py`
Expected: PASS

### Task 2: Extend Research State and Add Phase 5 Nodes

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\services\research\state.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\services\research\nodes.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_research_nodes_phase5.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:
- plan success and fallback
- reflect pass and revise
- revise_report
- recall_memory with and without session data
- save_memory invoking persistence

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_research_nodes_phase5.py`
Expected: FAIL because the new node factories do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Extend `ResearchState` with `NotRequired` Phase 5 fields and add the five node factories. Keep all Phase 4 node signatures intact.

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_research_nodes_phase5.py`
Expected: PASS

### Task 3: Add the `agent_v2` Graph

**Files:**
- Create: `E:\programs\AI_Agent_program\8w-plan\app\services\research\agent_v2.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\services\research\__init__.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_research_agent_v2.py`

- [ ] **Step 1: Write the failing tests**

Add integration tests for:
- direct pass path
- one-shot revision path
- with memory session
- without memory session
- forced exit at max iterations

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_research_agent_v2.py`
Expected: FAIL because `run_agent_v2` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Build the new LangGraph flow with:
- recall
- plan
- existing search/evaluate/refine/report nodes
- reflect
- optional revise
- save memory

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_research_agent_v2.py`
Expected: PASS

### Task 4: Integrate API and Memory Endpoints

**Files:**
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\schemas\research.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\api\routes\research.py`
- Create: `E:\programs\AI_Agent_program\8w-plan\app\api\routes\memory.py`
- Modify: `E:\programs\AI_Agent_program\8w-plan\app\main.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_research_endpoint_phase5.py`
- Test: `E:\programs\AI_Agent_program\8w-plan\tests\test_memory_endpoint.py`

- [ ] **Step 1: Write the failing tests**

Add route tests for:
- `mode="agent_v2"`
- `session_id` handling
- insight listing/search
- session fetch/clear
- clearing all long-term insights

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n ai-agent pytest -q tests/test_research_endpoint_phase5.py tests/test_memory_endpoint.py`
Expected: FAIL because the route/schema support does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Extend research schema/route, add memory route, register router in `main.py`, and provide a shared route-level `MemoryService`.

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n ai-agent pytest -q tests/test_research_endpoint_phase5.py tests/test_memory_endpoint.py`
Expected: PASS

### Task 5: Backward Compatibility Verification

**Files:**
- Verify only

- [ ] **Step 1: Run targeted Phase 5 tests**

Run: `conda run -n ai-agent pytest -q tests/test_memory_service.py tests/test_research_nodes_phase5.py tests/test_research_agent_v2.py tests/test_research_endpoint_phase5.py tests/test_memory_endpoint.py`
Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `conda run -n ai-agent pytest -q`
Expected: PASS with all pre-existing Phase 4 tests still green.

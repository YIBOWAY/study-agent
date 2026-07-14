# Phase F3: LangChain Parts 5–7 + Capstone — Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver LangChain track Parts 5–7 (Workbench product surface, framework comparisons with real LC experience, production-readiness contracts) plus an offline LC Capstone that composes Parts 1–7—without `research_core` mix or main CI breakage.

**Architecture:** Teaching-only `langchain_course` modules project inspectable LC domain objects into a JSON-compatible workbench snapshot, score build-vs-adopt decisions with transparent weights, and provide offline diagnostics / JSONL step store / approval+sandbox policies. Capstone under `course/tracks/langchain/capstone/` composes these contracts offline (scripted agent steps; no live key required for unit gate).

**Tech Stack:** Same as F1/F2 (`langchain-core`, `langchain-openai`, `python-dotenv`, pytest, ruff). No LangGraph.

**Spec:** `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`

## Global Constraints

- Zero import between `langchain_course` and `research_core`.
- Secrets only via env / gitignored `.env`.
- Main `pytest -q` stays offline green without LC group or key.
- LC track still must not require `langgraph`.
- Chinese user-facing track docs; agent commits/pushes.

---

### Task 1: Part 5 code — workbench snapshot

**Files:**
- Create: `packages/langchain_course/src/langchain_course/workbench.py`
- Create: `packages/langchain_course/tests/test_workbench.py`

**Interfaces:**
- `WorkbenchProject`, `WorkbenchRun`, panel item types
- `WorkbenchTimelineItem.from_step(step, *, run_id, index)` from `AgentStep`
- `WorkbenchSnapshot` with nine record keys + referential integrity
- `build_demo_snapshot()` offline demo
- every public item exposes `to_record()`

- [x] Implement + unit tests offline

### Task 2: Part 6 code — comparisons

**Files:**
- Create: `packages/langchain_course/src/langchain_course/comparisons.py`
- Create: `packages/langchain_course/tests/test_comparisons.py`

**Interfaces:**
- `SCORE_CRITERIA`, `ComparisonTask`, `FrameworkProfile`, `FrameworkRecommendation`
- `default_framework_profiles()` including handwritten / langchain / langgraph records
- `score_profile_for_task`, `build_recommendation_matrix`, `recommend_profile`
- `run_lc_baseline(task)` via scripted `AgentRunResult` (no live model)

- [x] Implement + unit tests offline

### Task 3: Part 7 code — production contracts

**Files:**
- Create: `packages/langchain_course/src/langchain_course/production.py`
- Create: `packages/langchain_course/tests/test_production.py`

**Interfaces:**
- `RunDiagnostics.from_steps(run_id, steps: Sequence[AgentStep])`
- `JsonlStepStore` append/read by run_id
- `ApprovalPolicy` / `SandboxPolicy` with typed decisions

- [x] Implement + unit tests offline

### Task 4: Course materials Parts 5–7

**Files:**
- Create chapters/labs/solutions 05–07 under `course/tracks/langchain/`
- Update README progress + handwritten-mapping.md

- [x] Materials

### Task 5: LC Capstone

**Files:**
- Create: `course/tracks/langchain/capstone/` (README, rubric, fixtures, skill, starter, solution, tests)

- [x] Capstone offline compose + tests

### Task 6: Indexes, verify, complete, push

```bash
uv run pytest packages/langchain_course/tests -q
uv run pytest course/tracks/langchain/capstone -q
uv run pytest -q
uv run ruff check .
uv run pytest tests/course/test_docs_freshness.py -q
```

- [x] Mark phase complete; commit; push; stop before F4

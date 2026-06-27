# Framework Comparisons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline, controlled framework-comparison slice that compares the handwritten `AgentRunner` against selected framework profiles on shared tasks, trajectory metrics, and recommendation criteria without moving framework code into the product runtime path.

**Architecture:** Phase 6 keeps `packages/research_core` and product apps framework-independent. Comparison code and reports live under `course/framework_comparisons/`; tests live under `tests/course/`. The handwritten runner path executes real `AgentRunner` fixtures with `FakeModel` and `ToolRuntime`. External framework candidates are represented as deterministic comparison profiles and mapping reports, not imported dependencies.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, JSON-compatible records, markdown reports.

---

## Product Slice

Included:

- a Phase 6 executable plan and progress record;
- deterministic comparison task specs under `course/framework_comparisons/`;
- an executable handwritten-runner baseline for the same task fixtures;
- framework profile records for PydanticAI, LlamaIndex Workflows, LangGraph, OpenAI Agents SDK, and CrewAI;
- recommendation-matrix helpers that score candidates by inspectability, testability, state/resume fit, product-boundary risk, and team cost;
- markdown reports under `course/framework_comparisons/`;
- Course Chapter/Lab/Solution 06 for framework comparison literacy;
- docs, roadmap, progress, README, and AGENTS synchronization.

Deferred:

- installing or importing third-party agent frameworks;
- replacing `research_core.runtime.AgentRunner`;
- product runtime integration with any framework;
- live provider or network-backed framework smoke tests;
- MCP or real A2A protocol implementation beyond the existing local A2A stub.

## File Structure

Create or update these files:

- Create: `redesign/docs/plans/2026-06-27-phase-6-framework-comparisons.md`
- Create: `redesign/course/framework_comparisons/__init__.py`
- Create: `redesign/course/framework_comparisons/common.py`
- Create: `redesign/course/framework_comparisons/reports/recommendation-matrix.md`
- Create: `redesign/course/framework_comparisons/reports/echo-tool-task.md`
- Create: `redesign/tests/course/test_framework_comparisons.py`
- Create: `redesign/course/chapters/06-framework-comparisons.md`
- Create: `redesign/course/labs/06-framework-comparisons-lab.md`
- Create: `redesign/course/solutions/06-framework-comparisons-solution.md`
- Modify: `redesign/course/framework_comparisons/.gitkeep`
- Modify: `redesign/course/README.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/course/roadmap.md`
- Modify: `redesign/docs/living-landscape.md`
- Modify: `redesign/docs/architecture/overview.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-6.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy root `app/`, `frontend/`, root `tests/`, root `eval/`, provider SDK code, or `packages/research_core` runtime code.

## Contracts

### Comparison Tasks

- `ComparisonTask`: a stable task spec with an ID, title, prompts, required capabilities, expected event sequence, and scoring weights.
- `TaskRunSummary`: the executable result of the handwritten runner on one task, including final answer, event sequence, tool-call count, error count, and a JSON-compatible record.
- `build_echo_tool_task()`: the first shared task fixture. It exercises a model tool call, tool result, final answer, and trajectory inspection.
- `run_handwritten_task(task)`: executes the task through `AgentRunner`, `FakeModel`, and `ToolRuntime`.

### Framework Profiles

- `FrameworkProfile`: a deterministic candidate profile with scores and notes for inspectability, offline testing, state/resume fit, typed contracts, multi-agent fit, product-boundary risk, and team cost.
- `default_framework_profiles()`: includes `handwritten`, `pydantic-ai`, `llamaindex-workflows`, `langgraph`, `openai-agents-sdk`, and `crewai`.
- Profiles are comparison records only. They must not import the actual frameworks.

### Recommendation Matrix

- `FrameworkRecommendation`: one task/profile score with strengths, tradeoffs, and total score.
- `build_recommendation_matrix(tasks, profiles)`: returns deterministic task/profile records.
- `recommend_profile(matrix, task_id)`: returns the highest-scoring profile for a task.
- Matrix records must be JSON-compatible and stable for course/lab checks.

## Task 1: Add Phase 6 Plan and Start Progress

**Files:**

- Create: `redesign/docs/plans/2026-06-27-phase-6-framework-comparisons.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-6.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Save this Phase 6 plan**

Save this plan at `redesign/docs/plans/2026-06-27-phase-6-framework-comparisons.md`.

- [x] **Step 2: Mark Phase 6 as active**

Update the progress dashboard:

- active branch: `codex/redesign-phase-6`;
- active phase: `Phase 6 - Framework Comparisons`;
- verification baseline: Phase 6 start from Phase 5 completion baseline, `173 passed`, `ruff check .` clean, and `apps/web` Vite build clean with `46 modules transformed`.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "phase-6-framework-comparisons|Phase 6|Framework Comparisons" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: Phase 6 plan and active progress state are discoverable from docs index, roadmap, and progress dashboard.

## Task 2: Add Offline Comparison Harness

**Files:**

- Create: `redesign/course/framework_comparisons/__init__.py`
- Create: `redesign/course/framework_comparisons/common.py`
- Create: `redesign/tests/course/test_framework_comparisons.py`
- Modify: `redesign/docs/progress/phases/phase-6.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- the public comparison names are exported;
- `build_echo_tool_task()` returns a task with a stable expected event sequence;
- `run_handwritten_task()` executes the task through real `AgentRunner` contracts and records the expected trajectory;
- profile records reject blank IDs and out-of-range scores;
- the recommendation matrix is JSON-compatible, deterministic, and recommends `handwritten` for the simple echo-tool task;
- `langgraph` is recommended for a state/resume-heavy task because the task weights state/resume above local inspectability.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/course/test_framework_comparisons.py -q
```

Expected: failure because `course.framework_comparisons` does not expose the comparison contracts.

- [ ] **Step 3: Implement comparison harness**

Implement frozen dataclasses and deterministic helpers in `course/framework_comparisons/common.py`. Keep all records JSON-compatible. Use the real `AgentRunner`, `FakeModel`, and `ToolRuntime` only for the handwritten baseline.

- [ ] **Step 4: Export comparison contracts**

Update `course/framework_comparisons/__init__.py`.

- [ ] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/course/test_framework_comparisons.py -q
cd redesign && uv run ruff check course/framework_comparisons tests/course/test_framework_comparisons.py
git diff --check
```

Expected: tests pass, ruff reports `All checks passed!`, and whitespace check is clean.

## Task 3: Add Comparison Reports and Course 06

**Files:**

- Create: `redesign/course/framework_comparisons/reports/recommendation-matrix.md`
- Create: `redesign/course/framework_comparisons/reports/echo-tool-task.md`
- Create: `redesign/course/chapters/06-framework-comparisons.md`
- Create: `redesign/course/labs/06-framework-comparisons-lab.md`
- Create: `redesign/course/solutions/06-framework-comparisons-solution.md`
- Modify: `redesign/course/README.md`
- Modify: `redesign/docs/course/roadmap.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/phases/phase-6.md`

- [ ] **Step 1: Add framework comparison reports**

Write reports that explain the shared echo-tool task, the state/resume-heavy task, the matrix criteria, and the recommendation results. Be explicit that Phase 6 compares framework fit without importing frameworks.

- [ ] **Step 2: Add learner-facing Chapter/Lab/Solution 06**

Chapter 06 must explain:

- why framework comparison comes after handwritten mechanism learning;
- how to compare frameworks on the same task instead of comparing marketing claims;
- how to inspect trajectories and task weights;
- why framework code stays out of `research_core` and product runtime paths.

Lab 06 should ask learners to:

- run the focused comparison tests;
- inspect the handwritten echo-tool trajectory;
- print the recommendation matrix;
- deliberately change task weights and observe the recommendation change.

- [ ] **Step 3: Update course indexes**

Update course entrypoint, docs course roadmap, and docs index so Chapter/Lab/Solution 06 and comparison reports are discoverable.

- [ ] **Step 4: Verify docs**

Run:

```bash
rg -n "06-framework-comparisons|FrameworkRecommendation|recommendation matrix|echo-tool task|course/framework_comparisons" redesign/course redesign/docs
```

Expected: Phase 6 concepts are discoverable from course, reports, docs index, and roadmap.

## Task 4: Sync Architecture, Glossary, README, AGENTS, and Progress

**Files:**

- Modify: `redesign/docs/architecture/overview.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/living-landscape.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-6.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Update architecture and glossary**

Document the Phase 6 comparison boundary and define `ComparisonTask`, `FrameworkProfile`, `FrameworkRecommendation`, and recommendation matrix.

- [ ] **Step 2: Update living landscape and root guidance**

Record the 2026-06-27 framework-comparison baseline in `docs/living-landscape.md`, update root README current scope, and update AGENTS rules so future agents keep framework code under `course/framework_comparisons/`.

- [ ] **Step 3: Update progress**

Mark Phase 6 complete only after final verification passes.

- [ ] **Step 4: Verify docs**

Run:

```bash
rg -n "ComparisonTask|FrameworkProfile|FrameworkRecommendation|framework code under course/framework_comparisons|Phase 6" redesign/docs redesign/README.md redesign/AGENTS.md
```

Expected: Phase 6 boundary and framework-comparison concepts are discoverable from architecture docs, glossary, root docs, and progress.

## Task 5: Final Phase 6 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-6.md`
- Modify: `redesign/docs/plans/2026-06-27-phase-6-framework-comparisons.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
cd redesign/apps/web && npm install && npm run build
git diff --check
```

Expected:

```text
All Python tests pass.
All ruff checks pass.
Vite build succeeds.
No whitespace errors.
```

- [ ] **Step 2: Clean generated side effects**

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, Python `__pycache__`, frontend `node_modules`, frontend `dist`, and TypeScript build info unless a file is an intentional source or lock artifact. Keep `apps/web/package-lock.json`.

- [ ] **Step 3: Commit and push**

Commit with a message that records Phase 6 deliverables and verification commands. Push branch `codex/redesign-phase-6`.

## Phase 6 Completion Checklist

- [ ] Phase 6 plan and progress records are active and indexed.
- [ ] Offline comparison harness is implemented under `course/framework_comparisons/`.
- [ ] Handwritten runner baseline executes the shared echo-tool task through `AgentRunner`.
- [ ] Framework profiles and recommendation matrix are deterministic and JSON-compatible.
- [ ] Comparison reports exist under `course/framework_comparisons/reports/`.
- [ ] Course Chapter/Lab/Solution 06 exists.
- [ ] Course docs, architecture docs, glossary, README, AGENTS, roadmap, and progress docs are updated.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] `cd redesign/apps/web && npm run build` passes.
- [ ] `git diff --check` is clean.
- [ ] No legacy root `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.

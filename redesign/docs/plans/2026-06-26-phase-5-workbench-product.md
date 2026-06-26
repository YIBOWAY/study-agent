# Workbench Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first local Research Agent Workbench product surface: deterministic product snapshot contracts, FastAPI read APIs, a React + TypeScript workbench, and matching learner-facing course material.

**Architecture:** Phase 5 keeps `research_core` independent from FastAPI and React by introducing pure Python workbench snapshot contracts under `research_core.product`. `apps/api` exposes those contracts through FastAPI, while `apps/web` renders the operational workspace through Vite/React using the API record shape and an offline fallback fixture.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, FastAPI, React, TypeScript, Vite, lucide-react, CSS modules/plain CSS.

---

## Product Slice

This phase builds a deterministic V1 product slice, not a full SaaS system.

Included:

- workbench snapshot contract for project, run, timeline, delegation, sources, report, memory, skills, and eval panels;
- FastAPI app with `/health`, `/api/workbench/snapshot`, and `/api/workbench/timeline`;
- React + TypeScript workbench first screen with navigation, task composer, run timeline, delegation tree, source/evidence panel, report editor, memory, skills, and eval panels;
- Chapter/Lab/Solution 05 teaching the product integration layer;
- docs/progress/roadmap synchronization.

Deferred:

- persistence and database migrations;
- authentication and multi-tenant accounts;
- real provider, real retrieval, and streaming adapters;
- SSE/websocket timeline streaming;
- editing APIs and report export;
- async delegation execution and remote A2A transport.

## File Structure

Create or update these files:

- Create: `redesign/packages/research_core/src/research_core/product/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/product/workbench.py`
- Create: `redesign/tests/research_core/test_workbench_snapshot.py`
- Create: `redesign/apps/api/src/research_api/__init__.py`
- Create: `redesign/apps/api/src/research_api/main.py`
- Create: `redesign/tests/apps/test_workbench_api.py`
- Create: `redesign/apps/web/package.json`
- Create: `redesign/apps/web/tsconfig.json`
- Create: `redesign/apps/web/vite.config.ts`
- Create: `redesign/apps/web/index.html`
- Create: `redesign/apps/web/src/App.tsx`
- Create: `redesign/apps/web/src/main.tsx`
- Create: `redesign/apps/web/src/styles.css`
- Create: `redesign/apps/web/src/types.ts`
- Create: `redesign/course/chapters/05-workbench-product.md`
- Create: `redesign/course/labs/05-workbench-product-lab.md`
- Create: `redesign/course/solutions/05-workbench-product-solution.md`
- Modify: `redesign/pyproject.toml`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/product/workbench.md`
- Modify: `redesign/docs/course/roadmap.md`
- Modify: `redesign/course/README.md`
- Modify: `redesign/docs/progress/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-5.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy root `app/`, `frontend/`, root `tests/`, root `eval/`, or provider SDK code.

## Task 1: Add Phase 5 Plan and Start Progress

**Files:**

- Create: `redesign/docs/plans/2026-06-26-phase-5-workbench-product.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-5.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Save this Phase 5 plan**

Save this plan at `redesign/docs/plans/2026-06-26-phase-5-workbench-product.md`.

- [x] **Step 2: Mark Phase 5 as active**

Update the progress dashboard:

- active branch: `codex/redesign-phase-5`;
- active phase: `Phase 5 - Workbench Product`;
- verification baseline: Phase 5 start from Phase 4 post-audit baseline, `160 passed`, `ruff check .` clean.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "phase-5-workbench-product|Phase 5|Workbench Product|FastAPI|React" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: Phase 5 plan and active progress state are discoverable from docs index, roadmap, and progress dashboard.

## Task 2: Add Workbench Snapshot Contracts

**Files:**

- Create: `redesign/packages/research_core/src/research_core/product/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/product/workbench.py`
- Create: `redesign/tests/research_core/test_workbench_snapshot.py`
- Modify: `redesign/docs/progress/phases/phase-5.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- `WorkbenchSnapshot.to_record()` returns JSON-compatible records with `project`, `run`, `timeline`, `delegation`, `sources`, `report`, `memory`, `skills`, and `evals`;
- timeline items preserve stable order and include `model_request`, `tool_call`, `delegate_start`, and `delegate_finish`;
- source/evidence/report records preserve claim-source links;
- memory/skill/eval panels expose deterministic summary rows;
- returned records are plain copies, so mutating them does not mutate the snapshot;
- invalid blank IDs/titles and non-JSON-compatible metadata are rejected.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_workbench_snapshot.py -q
```

Expected: failure because `research_core.product` does not exist.

- [ ] **Step 3: Implement snapshot contracts**

Implement frozen dataclasses and a deterministic `build_demo_workbench_snapshot()` helper.

Required contract names:

- `WorkbenchProject`
- `WorkbenchRun`
- `WorkbenchTimelineItem`
- `WorkbenchDelegationNode`
- `WorkbenchSourceItem`
- `WorkbenchReport`
- `WorkbenchMemoryItem`
- `WorkbenchSkillItem`
- `WorkbenchEvalItem`
- `WorkbenchSnapshot`
- `build_demo_workbench_snapshot`

Use existing `research_core.runtime`, `research_core.research`, `research_core.memory`, `research_core.skills`, and `research_core.delegation` record shapes where useful. Keep the module free of FastAPI, React, database, provider, and network imports.

- [ ] **Step 4: Export contracts**

Update `research_core.product.__init__` to export the public Phase 5 product contracts.

- [ ] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_workbench_snapshot.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/product tests/research_core/test_workbench_snapshot.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 3: Add FastAPI Workbench API

**Files:**

- Create: `redesign/apps/api/src/research_api/__init__.py`
- Create: `redesign/apps/api/src/research_api/main.py`
- Create: `redesign/tests/apps/test_workbench_api.py`
- Modify: `redesign/pyproject.toml`
- Modify: `redesign/docs/progress/phases/phase-5.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- `GET /health` returns `{"status": "ok", "service": "research-workbench-api"}`;
- `GET /api/workbench/snapshot` returns the full workbench snapshot record;
- `GET /api/workbench/timeline` returns only timeline records in the same order as the snapshot;
- OpenAPI includes `Workbench` tags for the product endpoints;
- API responses are JSON serializable and do not expose Python tuple/repr artifacts.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/apps/test_workbench_api.py -q
```

Expected: failure because `research_api` and FastAPI dependencies are not wired.

- [ ] **Step 3: Add dependencies and app code**

Update `pyproject.toml`:

- project dependencies: `fastapi>=0.115`;
- dev dependencies: `httpx>=0.27` for FastAPI TestClient;
- pytest `pythonpath`: add `apps/api/src`.

Implement `create_app()` and module-level `app` in `research_api.main`.

- [ ] **Step 4: Verify**

Run:

```bash
cd redesign && uv run pytest tests/apps/test_workbench_api.py -q
cd redesign && uv run ruff check apps/api/src tests/apps/test_workbench_api.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 4: Add React Workbench UI

**Files:**

- Create: `redesign/apps/web/package.json`
- Create: `redesign/apps/web/tsconfig.json`
- Create: `redesign/apps/web/vite.config.ts`
- Create: `redesign/apps/web/index.html`
- Create: `redesign/apps/web/src/App.tsx`
- Create: `redesign/apps/web/src/main.tsx`
- Create: `redesign/apps/web/src/styles.css`
- Create: `redesign/apps/web/src/types.ts`
- Modify: `redesign/docs/progress/phases/phase-5.md`

- [ ] **Step 1: Create the app shell**

Use Vite + React + TypeScript. The first viewport must be the actual workbench, not a marketing landing page.

Required first-screen regions:

- workspace navigation;
- task composer;
- run timeline;
- delegation tree;
- source/evidence panel;
- report editor;
- memory panel;
- skills panel;
- eval panel.

- [ ] **Step 2: Implement data loading**

`App.tsx` should fetch `/api/workbench/snapshot` and fall back to a deterministic local fixture when the API is unavailable. The fallback must use the same TypeScript `WorkbenchSnapshot` shape as the API.

- [ ] **Step 3: Implement polished operational layout**

Use dense, scan-friendly product UI:

- no landing hero;
- no nested cards;
- no decorative gradient orbs;
- no one-note palette;
- use lucide icons for navigation/tool buttons;
- stable dimensions for timeline, panels, and navigation;
- responsive layout for desktop and mobile.

- [ ] **Step 4: Verify**

Run:

```bash
cd redesign/apps/web && npm install
cd redesign/apps/web && npm run build
```

Expected: Vite TypeScript build succeeds.

## Task 5: Add Course 05 and Product Docs

**Files:**

- Create: `redesign/course/chapters/05-workbench-product.md`
- Create: `redesign/course/labs/05-workbench-product-lab.md`
- Create: `redesign/course/solutions/05-workbench-product-solution.md`
- Modify: `redesign/course/README.md`
- Modify: `redesign/docs/course/roadmap.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/product/workbench.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/phases/phase-5.md`

- [ ] **Step 1: Add learner-facing product integration material**

Chapter 05 must explain:

- why product adapters sit between `research_core` and FastAPI/React;
- how a workbench snapshot differs from raw runtime/domain objects;
- how the API and UI can be tested without real providers;
- how to inspect timeline, delegation, evidence, memory, skills, and eval panels.

- [ ] **Step 2: Add a hands-on lab and solution**

Lab 05 should ask learners to:

- call the API test client;
- inspect a snapshot record;
- run the web build;
- deliberately mutate a returned snapshot record and verify the product contract remains stable.

- [ ] **Step 3: Update docs and progress**

Update course index, docs index, product boundary docs, root README, AGENTS rules, and progress logs.

- [ ] **Step 4: Verify**

Run:

```bash
rg -n "05-workbench-product|WorkbenchSnapshot|research_api|apps/web|FastAPI|React" redesign/course redesign/docs redesign/README.md redesign/AGENTS.md
```

Expected: Phase 5 product concepts are discoverable from course, docs, and root project guidance.

## Task 6: Final Phase 5 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-5.md`
- Modify: `redesign/docs/plans/2026-06-26-phase-5-workbench-product.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
cd redesign/apps/web && npm run build
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

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, Python `__pycache__`, and frontend `node_modules`/`dist` build output unless a file is an intentional source or lock artifact. Keep `apps/web/package-lock.json` if `npm install` creates it.

- [ ] **Step 3: Commit and push**

Commit with a message that records Phase 5 deliverables and verification commands. Push branch `codex/redesign-phase-5`.

## Phase 5 Completion Checklist

- [ ] Workbench snapshot contracts are implemented and exported.
- [ ] Snapshot records cover project, run, timeline, delegation, sources, report, memory, skills, and eval panels.
- [ ] FastAPI API exposes health, snapshot, and timeline endpoints.
- [ ] React workbench first screen is an operational workspace, not a landing page.
- [ ] Web build passes.
- [ ] Course Chapter/Lab/Solution 05 exists.
- [ ] Product docs, architecture docs, README, AGENTS, roadmap, and progress docs are updated.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] `cd redesign/apps/web && npm run build` passes.
- [ ] `git diff --check` is clean.
- [ ] No legacy root `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.

# Phase 5 Progress: Workbench Product

Status: Complete

Started: 2026-06-26
Completed: 2026-06-27
Branch: `codex/redesign-phase-5`

## Goal

Add the FastAPI product API and React workbench that expose research run timelines, delegation trees, evidence, reports, memory, skills, and evals.

## Start Conditions

- Runtime events are stable enough for UI surfaces.
- Research and delegation contracts are available.

## Planned Deliverables

- Phase 5 executable plan under `redesign/docs/plans/`.
- Pure `research_core.product` workbench snapshot contracts.
- FastAPI app under `apps/api` exposing workbench health, snapshot, and timeline endpoints.
- React + TypeScript + Vite workbench under `apps/web`.
- Course Chapter/Lab/Solution 05 for product integration.
- Product docs, course roadmap, README, AGENTS, and progress sync.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-26 | Phase 5 started from the Phase 4 post-audit baseline. Verification before changes: `uv run pytest -q` -> `160 passed`; `uv run ruff check .` -> `All checks passed!`. |
| 2026-06-26 | Task 2 added pure `research_core.product` workbench snapshot contracts and deterministic demo data. Red check: focused pytest failed with `ModuleNotFoundError: No module named 'research_core.product'`; green checks: `tests/research_core/test_workbench_snapshot.py -q` -> `8 passed`, targeted `ruff check` -> `All checks passed!`. |
| 2026-06-26 | Task 3 added the FastAPI workbench API under `apps/api`. Red check: focused pytest failed with `ModuleNotFoundError: No module named 'fastapi'`; green checks: `tests/apps/test_workbench_api.py -q` -> `5 passed`, targeted `ruff check apps/api/src tests/apps/test_workbench_api.py` -> `All checks passed!`. |
| 2026-06-26 | Task 4 added the Vite + React + TypeScript workbench under `apps/web` with API snapshot loading and a deterministic fallback fixture. Verification: `npm install` -> `added 25 packages`; `npm run build` -> TypeScript and Vite build passed with `46 modules transformed`; browser check at `http://127.0.0.1:5173/` with FastAPI on `127.0.0.1:8000` -> desktop/mobile rendered 8 panels, data source `api`, no horizontal overflow, no console warnings or errors. |
| 2026-06-27 | Task 5 added Course Chapter/Lab/Solution 05 for Workbench Product and synchronized learner/product docs. The lesson now explains `WorkbenchSnapshot`, why product adapters sit between `research_core` and FastAPI/React, how API/UI can be tested without real providers, and how to inspect timeline, delegation, evidence, report, memory, skills, and eval panels. Verification: course/docs/root grep for Phase 5 product concepts passed; focused workbench pytest -> `13 passed`; targeted `ruff check` -> `All checks passed!`; `npm install && npm run build` -> Vite build passed with `46 modules transformed`; `git diff --check` clean. |
| 2026-06-27 | Phase 5 completed after neat-freak docs reconciliation. Final verification: `uv run pytest -q` -> `173 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`; `git diff --check` clean. Generated `.venv`, caches, `uv.lock`, `node_modules`, `dist`, TypeScript build info, and Python `__pycache__` outputs were removed before final commit. |
| 2026-06-29 | Post-phase review remediation accepted the Workbench API consistency, public evidence type, and snapshot cross-field invariant findings. The fix exposes `WorkbenchEvidenceItem`, validates run/project, timeline/run, report/run, source/evidence, report-link/evidence, and delegation tree relationships, and makes `/api/workbench/snapshot` plus `/api/workbench/timeline` derive from one app-level demo snapshot. Combined review verification: focused review suite -> `39 passed`; full `uv run pytest -q` -> `185 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`. |

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm run build
```

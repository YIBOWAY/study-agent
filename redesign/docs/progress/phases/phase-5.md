# Phase 5 Progress: Workbench Product

Status: In Progress

Started: 2026-06-26
Completed: Not completed
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

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm run build
```

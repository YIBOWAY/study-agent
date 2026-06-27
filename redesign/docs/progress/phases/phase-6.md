# Phase 6 Progress: Framework Comparisons

Status: Complete

Started: 2026-06-27
Completed: 2026-06-27
Branch: `codex/redesign-phase-6`

## Goal

Compare the handwritten runner against selected agent frameworks on the same tasks, fixtures, and trajectory metrics.

## Start Conditions

- Workbench and core research flows are stable enough to provide comparison tasks.
- Framework code can remain isolated under `course/framework_comparisons/`.

## Planned Deliverables

- Phase 6 executable plan under `redesign/docs/plans/`.
- Offline comparison harness under `course/framework_comparisons/`.
- Handwritten `AgentRunner` baseline for the shared echo-tool task.
- Deterministic framework profiles and recommendation matrix.
- Comparison reports under `course/framework_comparisons/reports/`.
- Course Chapter/Lab/Solution 06 for framework comparison literacy.
- Architecture docs, glossary, root README, AGENTS, roadmap, and progress sync.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-27 | Phase 6 started from Phase 5 baseline. Verification before changes: `uv run pytest -q` -> `173 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`. |
| 2026-06-27 | Task 2 added the offline framework comparison harness under `course/framework_comparisons/` with a real handwritten `AgentRunner` echo-tool baseline, deterministic framework profiles, and recommendation-matrix helpers. Red check: `uv run pytest tests/course/test_framework_comparisons.py -q` failed with `ModuleNotFoundError: No module named 'course'`, then exposed recommendation contract fixes. Green checks: focused pytest -> `6 passed`; `uv run ruff check course/framework_comparisons tests/course/test_framework_comparisons.py pyproject.toml` -> `All checks passed!`. |
| 2026-06-27 | Task 3 added framework comparison reports plus Course Chapter/Lab/Solution 06. The learner path now explains why comparisons need shared tasks, fake fixtures, trajectory checks, task weights, and product-boundary discipline. |
| 2026-06-27 | Task 4 synchronized architecture docs, glossary, living landscape, root README, AGENTS, and overall progress with the Phase 6 comparison boundary. Framework comparison code is documented as course material under `course/framework_comparisons/`, not product runtime dependency. |
| 2026-06-27 | Phase 6 completed after neat-freak docs reconciliation. Final verification: `uv run pytest -q` -> `179 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`; `git diff --check` clean. Generated `.venv`, caches, `uv.lock`, `node_modules`, `dist`, TypeScript build info, and Python `__pycache__` outputs were removed before final commit. |

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm install && npm run build
```

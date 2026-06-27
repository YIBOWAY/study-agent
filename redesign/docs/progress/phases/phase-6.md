# Phase 6 Progress: Framework Comparisons

Status: In Progress

Started: 2026-06-27
Completed: Not completed
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

# Phase R5 Progress: Course Teaching Redesign - Part 5

Status: In Progress

Started: 2026-07-01
Branch: `codex/redesign-course-r5`

## Goal

Rewrite Part 5 so Workbench Product teaches the product-adapter boundary (raw domain objects -> `WorkbenchSnapshot` -> FastAPI read API -> React panels) through the local paper research assistant's "give the researcher an inspectable workbench without inventing a separate data model" problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phases R1-R4 are complete and established the project-driven course format plus the markdown Python block gate covering Parts 1-4.
- Phase R5 starts from `docs/plans/2026-07-01-phase-r5-course-teaching-redesign.md`.
- First-principles review verified the real `research_core.product` surface the v1 material does not teach: the `from_*` adapters, `summary_row()` projections, and the `_validate_snapshot_references` referential-integrity failures.
- Verified gate constraint: the markdown gate helper `_ensure_research_core_on_path` only adds `packages/research_core/src`, so Part 5's API blocks (`from research_api.main import create_app`) need `apps/api/src` on `sys.path` too. Confirmed `ModuleNotFoundError: No module named 'research_api'` without it.

## Execution Refinement

To keep every commit's gate green, the `apps/api/src` path extension lands in Task 2, but the three Part 5 course files are added to `COURSE_MARKDOWN_PATHS` in Task 6 (after Tasks 3-5 rewrite them into gate-executable blocks), not in Task 2.

## Task Checklist

- [x] Task 1: Start R5 plan and progress.
- [x] Task 2: Extend the markdown Python block gate to support `apps/api/src` on the path.
- [ ] Task 3: Rewrite Chapter 05 as project-driven Part 5 material.
- [ ] Task 4: Rewrite Lab 05 with L1/L2/L3 exercises and feedback loops.
- [ ] Task 5: Rewrite Solution 05 with runnable assertions and design rationale.
- [ ] Task 6: Add Part 5 files to the gate and sync course indexes and progress.
- [ ] Task 7: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [ ] Chapter/Lab/Solution 05 are rewritten around the inspectable-workbench problem.
- [ ] Part 5 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [ ] Chapter 05 teaches the mental model: dashboard + stable snapshot contract + `from_*` adapters + referential validation + downward-only three-layer boundary.
- [ ] Chapter/Lab/Solution 05 exercise the `from_*` adapters, `summary_row()` projections, referential-integrity failures, and the FastAPI transport/React fallback boundary.
- [ ] Lab 05 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [ ] Solution 05 provides runnable L1/L2 answers plus one valid L3 reference design and required invariants.
- [ ] The markdown Python block gate covers Part 5 (or API blocks are explicitly documented as gate-excluded and covered by `tests/apps/test_workbench_api.py`).
- [ ] Docs index, course roadmap, course README, and overall progress are synced.
- [ ] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R5 started after first-principles review of the R5 plan, the current Part 5 v1 material gaps, and the real `research_core.product` / `apps/api` contracts. Execution uses the subagent-driven workflow: a coordinator handles docs bookkeeping (Tasks 1, 6, and final verification), implementer/writer subagents handle the gate change and the chapter/lab/solution rewrites, and task-reviewer plus a final whole-branch code-reviewer subagent gate quality. |
| 2026-07-01 | Task 1 landed (commit `ad14aa3`): R5 plan, phase-r5 progress record, and docs/progress index updates marking R5 in progress. |
| 2026-07-01 | Task 2 landed (commit `2a682cb`): the markdown gate helper now also puts `apps/api/src` on `sys.path` when present, with a monkeypatch-isolated RED->GREEN test proving an `apps/api` import block executes (gate 4 -> 5 passing). Task reviewer approved with one Minor symlink-resolution hardening note recorded for the final whole-branch review. Part 5 files are intentionally not yet in `COURSE_MARKDOWN_PATHS`; that lands in Task 6. |

## Verification Target

Run from `redesign/` unless noted:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

## Verification Results

Recorded during Task 7.

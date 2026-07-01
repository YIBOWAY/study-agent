# Phase R5 Progress: Course Teaching Redesign - Part 5

Status: Complete

Started: 2026-07-01
Completed: 2026-07-01
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
- [x] Task 3: Rewrite Chapter 05 as project-driven Part 5 material.
- [x] Task 4: Rewrite Lab 05 with L1/L2/L3 exercises and feedback loops.
- [x] Task 5: Rewrite Solution 05 with runnable assertions and design rationale.
- [x] Task 6: Add Part 5 files to the gate and sync course indexes and progress.
- [x] Task 7: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [x] Chapter/Lab/Solution 05 are rewritten around the inspectable-workbench problem.
- [x] Part 5 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [x] Chapter 05 teaches the mental model: dashboard + stable snapshot contract + `from_*` adapters + referential validation + downward-only three-layer boundary.
- [x] Chapter/Lab/Solution 05 exercise the `from_*` adapters, `summary_row()` projections, referential-integrity failures, and the FastAPI transport/React fallback boundary.
- [x] Lab 05 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [x] Solution 05 provides runnable L1/L2 answers plus one valid L3 reference design and required invariants.
- [x] The markdown Python block gate covers Part 5 (or API blocks are explicitly documented as gate-excluded and covered by `tests/apps/test_workbench_api.py`).
- [x] Docs index, course roadmap, course README, and overall progress are synced.
- [x] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R5 started after first-principles review of the R5 plan, the current Part 5 v1 material gaps, and the real `research_core.product` / `apps/api` contracts. Execution uses the subagent-driven workflow: a coordinator handles docs bookkeeping (Tasks 1, 6, and final verification), implementer/writer subagents handle the gate change and the chapter/lab/solution rewrites, and task-reviewer plus a final whole-branch code-reviewer subagent gate quality. |
| 2026-07-01 | Task 1 landed (commit `ad14aa3`): R5 plan, phase-r5 progress record, and docs/progress index updates marking R5 in progress. |
| 2026-07-01 | Task 2 landed (commit `2a682cb`): the markdown gate helper now also puts `apps/api/src` on `sys.path` when present, with a monkeypatch-isolated RED->GREEN test proving an `apps/api` import block executes (gate 4 -> 5 passing). Task reviewer approved with one Minor symlink-resolution hardening note recorded for the final whole-branch review. Part 5 files are intentionally not yet in `COURSE_MARKDOWN_PATHS`; that lands in Task 6. |
| 2026-07-01 | Task 3 landed (commits `59da98e` write, `a4bbc5d` fix): Chapter 05 rewritten around the inspectable-workbench problem with Learner Contract, two ASCII diagrams, eight callouts, all five `from_*` adapters, referential-integrity Break/Fix, and the FastAPI/React boundary. Gate self-check 16 blocks / 14 expected outputs matched. Task reviewer approved; the one Important finding (standalone `from_evidence` demo) and two Minors were fixed. |
| 2026-07-01 | Task 4 landed (commit `2ca02bf`): Lab 05 rewritten with L1 Follow, L2 Modify/Break-Fix (all five referential errors + copy safety), and an open-ended L3 Design whose self-check is a non-executed text block. Four-part feedback on each tier. Gate self-check 14 blocks / 10 matched. Task reviewer approved with two Minor notes recorded. |
| 2026-07-01 | Task 5 landed (commit `282e80a`): Solution 05 rewritten with runnable assert-based L1/L2/L3 answers, What This Proves / Why This Design per tier, Forward Connections mapping all four earlier Parts to panels, and Final Takeaway. Gate self-check 12 blocks, all asserts pass. Task reviewer approved with one Minor note recorded. |
| 2026-07-01 | Task 6 landed: Part 5 chapter/lab/solution added to `COURSE_MARKDOWN_PATHS` (markdown gate now covers Parts 0-5, `5 passed`; direct run 42 Part-5 blocks / 24 expected outputs matched). Course README, redesign README, roadmap, execution roadmap, and progress indexes now describe Part 5 as R5 rewritten while Parts 6-7 stay v1. Docs freshness + markdown gate `8 passed`. |
| 2026-07-01 | Task 7 completed final verification and whole-branch review. Coordinator verification: full `pytest -q` `204 passed`; `ruff check .` clean; docs freshness + markdown gate `8 passed`; `git diff --check` clean; `apps/web` `npm ci && npm run build` clean. A final whole-branch code-reviewer subagent returned READY WITH MINOR FOLLOW-UPS: the only blocker was this Task-7 progress closeout (now landed), and all four recorded per-task Minor findings were triaged acceptable-as-is. Generated `.venv`, `uv.lock`, `node_modules`, `dist`, TypeScript build info, and `__pycache__` outputs were removed before final status checks. |

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

Run from `redesign/` on 2026-07-01.

| Check | Result |
| --- | --- |
| `PYTHONPATH=packages/research_core/src uv run pytest -q` | `204 passed` |
| `PYTHONPATH=packages/research_core/src uv run ruff check .` | `All checks passed!` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` | `3 passed` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` | `5 passed` (Parts 0-5 + the `apps/api/src` path test) |
| Part 5 direct gate run (`python -m infra.markdown_python_blocks` on the 3 files) | Checked 42 Python blocks; 24 expected outputs matched. |
| `git diff --check` | Clean |
| `cd apps/web && npm ci && npm run build` | Passed; Vite built successfully. |
| Whole-branch code review | READY WITH MINOR FOLLOW-UPS; Task-7 closeout was the only blocker (now landed); four per-task Minor findings triaged acceptable-as-is. |

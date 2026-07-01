# Phase R6 Progress: Course Teaching Redesign - Part 6

Status: In Progress

Started: 2026-07-01
Branch: `codex/redesign-course-r6`

## Goal

Rewrite Part 6 so Framework Comparisons teaches how to make a defensible build-vs-adopt decision — pin the same task, fixture, and metric, then let a transparent weighted score decide — through the "why not just use LangChain/CrewAI?" problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phases R1-R5 are complete and established the project-driven course format and the markdown Python block gate (now covering Parts 0-5, including `apps/api/src` blocks).
- Phase R6 starts from `docs/plans/2026-07-01-phase-r6-course-teaching-redesign.md`.
- First-principles review verified the real `course.framework_comparisons` surface the v1 material under-teaches: the transparent weighted-score formula, the `>=0.8` strengths / `<0.55` tradeoffs derivation, the deterministic tie-break, and the controlled-metric failures.
- Verified gate constraint: unlike R5, Part 6 needs NO gate helper change. `course.framework_comparisons` already imports under the gate (redesign root on `sys.path` via the `python -m` cwd behaviour and via pytest `pythonpath = ["."]`). The v1-chapter gate run only failed on an uncaught `ValueError` block, confirming the import path is fine.

## Execution Note

R6 has no infra/gate code change (a deliberate contrast with R5's `apps/api/src` path change). The only gate work is adding the three Part 6 files to `COURSE_MARKDOWN_PATHS` in Task 5, after Tasks 2-4 rewrite them so every error block self-catches. Execution uses the subagent-driven workflow: a coordinator handles docs bookkeeping (Tasks 1, 5, and final verification), writer subagents handle the chapter/lab/solution rewrites, and task-reviewer plus a final whole-branch code-reviewer subagent gate quality.

## Task Checklist

- [ ] Task 1: Start R6 plan and progress.
- [ ] Task 2: Rewrite Chapter 06 as project-driven Part 6 material.
- [ ] Task 3: Rewrite Lab 06 with L1/L2/L3 exercises and feedback loops.
- [ ] Task 4: Rewrite Solution 06 with runnable assertions and design rationale.
- [ ] Task 5: Add Part 6 files to the gate and sync course indexes and progress.
- [ ] Task 6: Final verification, cleanup, whole-branch review, and docs reconciliation.

## Exit Signal

- [ ] Chapter/Lab/Solution 06 are rewritten around the build-vs-adopt decision problem.
- [ ] Part 6 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [ ] The rewrite makes the weighted score transparent (manual `total_score` reproduction, `>=0.8` strengths / `<0.55` tradeoffs derivation, deterministic tie-break).
- [ ] Lab 06 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [ ] Solution 06 provides runnable L1/L2 answers plus one valid L3 reference design and the required winner invariant.
- [ ] Every error-demonstrating block self-catches, and the markdown Python block gate covers Part 6 with no infra/gate helper change.
- [ ] Docs index, course roadmap, course README, redesign README, and overall progress are synced.
- [ ] Fresh verification results and a whole-branch review are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R6 started after first-principles review of the R6 plan, the current Part 6 v1 material gaps, and the real `course.framework_comparisons` contracts. Verified the gate imports `course.framework_comparisons` with no helper change, so R6 has no infra task. |

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

Recorded during Task 6.

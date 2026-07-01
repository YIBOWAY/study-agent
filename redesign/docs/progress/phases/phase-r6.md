# Phase R6 Progress: Course Teaching Redesign - Part 6

Status: Complete

Started: 2026-07-01
Completed: 2026-07-01
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

- [x] Task 1: Start R6 plan and progress.
- [x] Task 2: Rewrite Chapter 06 as project-driven Part 6 material.
- [x] Task 3: Rewrite Lab 06 with L1/L2/L3 exercises and feedback loops.
- [x] Task 4: Rewrite Solution 06 with runnable assertions and design rationale.
- [x] Task 5: Add Part 6 files to the gate and sync course indexes and progress.
- [x] Task 6: Final verification, cleanup, whole-branch review, and docs reconciliation.

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
| 2026-07-01 | Task 1 landed (commit `501fd68`): R6 plan, phase-r6 progress record, and docs/progress index updates marking R6 in progress. |
| 2026-07-01 | Task 2 landed (commit `69f2c21`): Chapter 06 rewritten around the build-vs-adopt decision with a transparent weighted score (by-hand `total_score` 0.854 reproduced and asserted equal to the record, plus the `>=0.8` strengths / `<0.55` tradeoffs derivation and the deterministic tie-break), Learner Contract, two ASCII diagrams, eight callouts, and five self-caught controlled-metric breaks. Gate self-check 14 blocks / 14 matched. Task reviewer approved with two Minor notes recorded. |
| 2026-07-01 | Task 3 landed (commits `8563bc1` write, `b1aa488` fix): Lab 06 rewritten with L1 Follow, L2 Modify (raise `state_resume` weight, predict-then-verify the winner flip, by-hand `total_score` check) plus five self-caught breaks, and an open-ended L3 Design whose self-check is a non-executed text block. Four-part feedback on each tier. Gate self-check 15 blocks / 11 matched. Task reviewer approved; a false-positive "missing Solution section" finding was resolved (the runnable L3 reference lives in the separate `course/solutions/06` file), and two Minor L2 weight-shift wording nits were fixed by the coordinator. |
| 2026-07-01 | Task 4 landed (commit `608ea30`): Solution 06 rewritten with runnable assert-based L1/L2/L3 answers (including a manual `total_score` reproduction and a runnable L3 reference design where langgraph beats the crewai decoy), What This Proves / Why This Design per tier, Forward Connections, and Final Takeaway. Gate self-check 12 blocks, all asserts pass. Task reviewer approved with one Minor note recorded. |
| 2026-07-01 | Task 5 landed: Part 6 chapter/lab/solution added to `COURSE_MARKDOWN_PATHS` (markdown gate now covers Parts 0-6, `5 passed`; direct run 41 Part-6 blocks / 25 expected outputs matched). Course README, redesign README, roadmap, execution roadmap, and progress indexes now describe Part 6 as R6 rewritten while Part 7 stays v1. |
| 2026-07-01 | Task 6 completed final verification and whole-branch review. Coordinator verification: full `pytest -q` `204 passed`; `ruff check .` clean; docs freshness + markdown gate `8 passed`; `git diff --check` clean; `apps/web` `npm ci && npm run build` clean. A whole-branch code-reviewer returned READY WITH MINOR FOLLOW-UPS with no Critical/Important findings; the two recorded Minor notes (the empty-weights Break rationale wording, consistent across all three files; and Solution Break E reusing the L1 `matrix` under the shared-namespace model) were both triaged acceptable-as-is. Generated artifacts were removed before final status checks. |

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
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` | `5 passed` (Parts 0-6) |
| Part 6 direct gate run (`python -m infra.markdown_python_blocks` on the 3 files) | Checked 41 Python blocks; 25 expected outputs matched. |
| `git diff --check` | Clean |
| `cd apps/web && npm ci && npm run build` | Passed; Vite built successfully. |
| Whole-branch code review | READY WITH MINOR FOLLOW-UPS; no Critical/Important; two Minor notes triaged acceptable-as-is. |

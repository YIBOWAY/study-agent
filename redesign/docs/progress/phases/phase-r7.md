# Phase R7 Progress: Course Teaching Redesign - Part 7

Status: In Progress

Started: 2026-07-02
Completed: TBD
Branch: `codex/redesign-course-r7`

## Goal

Rewrite Part 7 so Production Readiness teaches local-first production boundaries — diagnostics, JSONL persistence, approval policy, sandbox policy, and docs freshness — through the "can we replay, audit, and block unsafe runs before real deployment?" problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phases R1-R6 are complete and established the project-driven course format.
- The markdown Python block gate covers setup material plus Parts 1-6.
- Phase R7 starts from `docs/plans/2026-07-02-phase-r7-course-teaching-redesign.md`.
- Post-audit sync verified current Part 7 v1 material is direct-gate clean, but it has not yet been rewritten into the R1-R6 teaching structure.

## Execution Note

R7 is a teaching rewrite, not a runtime/product implementation phase. The existing `research_core.production` contracts are the teaching surface. Expected code changes are limited to course/docs/gate indexing unless implementation discovers a verified mismatch between documented behavior and tests.

## Task Checklist

- [x] Task 1: Start R7 plan and progress.
- [x] Task 2: Rewrite Chapter 07 as project-driven Part 7 material.
- [x] Task 3: Rewrite Lab 07 with L1/L2/L3 exercises and feedback loops.
- [x] Task 4: Rewrite Solution 07 with runnable assertions and design rationale.
- [x] Task 5: Add Part 7 files to the markdown gate and sync course indexes and progress.
- [ ] Task 6: Final verification, cleanup, whole-branch review, and docs reconciliation.

## Exit Signal

- [x] Chapter/Lab/Solution 07 are rewritten around the replay/audit/block-unsafe-runs problem.
- [x] Part 7 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [x] The rewrite teaches diagnostics, JSONL event replay, approval policy, sandbox policy, and docs freshness as inspectable local contracts.
- [x] Lab 07 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [x] Solution 07 provides runnable L1/L2 answers plus one valid L3 reference design and required production-readiness invariants.
- [x] Every error-demonstrating block self-catches, and the markdown Python block gate covers Part 7 with no helper change.
- [x] Docs index, course roadmap, course README, redesign README, execution roadmap, and overall progress are synced.
- [ ] Fresh verification results and a whole-branch review are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-02 | Phase R7 started from `codex/redesign-course-r7` after reviewing the R7 plan and the real `research_core.production` contracts. Codegraph status was up to date at start (65 files, 1,001 nodes, 2,751 edges). |
| 2026-07-02 | Task 2 landed: Chapter 07 rewritten around the replay/audit/block-unsafe-runs problem with a Learner Contract, local-first safety-desk mental model, two ASCII diagrams, six callouts, Build/Inspect/Break/Fix/Reflect flow, explicit docs-freshness and Capstone connections, and self-caught production-boundary failures. Direct chapter gate checked 12 Python blocks with 12 expected outputs matched. |
| 2026-07-02 | Task 3 landed: Lab 07 rewritten with L1 Follow (diagnostics, JSONL replay, approval/sandbox decisions), L2 Modify/Break-Fix (trajectory and policy changes plus seven production-boundary checks), and open-ended L3 Design for a report-export readiness boundary. Each tier includes Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct. Direct lab gate checked 16 Python blocks with 11 expected outputs matched. |
| 2026-07-02 | Task 4 landed: Solution 07 rewritten as L1/L2/L3 runnable answers with assert-based verification, per-tier What This Proves and Why This Design, one valid report-export reference design, and Capstone trust-evidence connections. Direct solution gate checked 3 Python blocks with 3 expected outputs matched. |
| 2026-07-02 | Task 5 landed: Part 7 chapter/lab/solution files were added to `tests/course/test_markdown_python_blocks.py`, course/docs/progress indexes now describe Part 7 as R7 rewritten material, the markdown Python block gate passed with `5 passed`, and docs freshness passed with `3 passed`. |

## Verification Target

Run from `redesign/` unless noted:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/07-production-readiness.md course/labs/07-production-readiness-lab.md course/solutions/07-production-readiness-solution.md --project-root .
git diff --check
cd apps/web && npm ci && npm run build
```

## Verification Results

Pending final R7 verification.

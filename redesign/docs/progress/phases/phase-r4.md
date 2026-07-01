# Phase R4 Progress: Course Teaching Redesign - Part 4

Status: In Progress

Started: 2026-07-01
Completed: TBD
Branch: `codex/redesign-course-r4`

## Goal

Rewrite Part 4 so Multi-Agent Delegation teaches child-context isolation, budget accounting, and unresolved-conflict visibility through the local paper research assistant's delegated-review problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phase R1 is complete and established the project-driven course format.
- Phase R2 is complete and established the Part 2 evidence-chain teaching pattern.
- Phase R3 is complete and established the Part 3 Memory/Skills pattern plus the markdown Python block verification gate.
- Phase R4 starts from `docs/plans/2026-07-01-phase-r4-course-teaching-redesign.md`.
- `codegraph status .` in `redesign/` reports the existing index is up to date with 65 files, 1,001 nodes, and 2,751 edges, so no fresh `codegraph init` is required.
- First-principles review accepted the R4 plan focus: teach the existing `research_core.delegation` contracts without changing runtime/product code, and expand the markdown Python block gate to cover Parts 1-4.

## Planned Deliverables

- R4 executable plan and progress record.
- Markdown Python fenced-block gate coverage for Parts 1-4.
- Part 4 chapter rewrite: `course/chapters/04-multi-agent-delegation.md`.
- Part 4 lab rewrite: `course/labs/04-delegation-runtime-lab.md`.
- Part 4 solution rewrite: `course/solutions/04-delegation-runtime-solution.md`.
- Course README, roadmap, docs index, and progress sync.
- Final verification, cleanup, and neat-freak docs reconciliation.

## Task Checklist

- [x] Task 1: Start R4 plan and progress.
- [x] Task 2: Extend markdown Python block gate to Parts 1-4.
- [x] Task 3: Rewrite Chapter 04 as project-driven Part 4 material.
- [x] Task 4: Rewrite Lab 04 with L1/L2/L3 exercises and feedback loops.
- [x] Task 5: Rewrite Solution 04 with runnable assertions and design rationale.
- [x] Task 6: Sync course indexes and progress after content lands.
- [ ] Task 7: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [ ] Chapter/Lab/Solution 04 are rewritten around the "delegate without leaking context, overspending budget, or hiding failures" problem.
- [ ] Part 4 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [ ] Chapter 04 teaches the delegation mental model: role badge, task sheet, budget, parent receipt trail, single-child result, and unresolved-conflict list.
- [ ] Chapter/Lab/Solution 04 exercise `run_task`, `run_many`, `max_total_steps` accounting, duplicate id rejection, `DelegationMergeResult.from_results`, context isolation via `compile_child_prompt`, and parent `delegate_*` events.
- [ ] Lab 04 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [ ] Solution 04 provides runnable L1/L2 answers plus one valid L3 reference design and required invariants.
- [ ] Markdown Python block gate covers Parts 1-4.
- [ ] Docs index, course roadmap, course README, and overall progress are synced.
- [ ] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R4 started after first-principles review of the R4 plan, current Part 4 material gaps, and the real `DelegationRuntime` / `DelegationMergeResult` contracts. Codegraph is initialized and up to date, so R4 can use the existing index without re-running `codegraph init`. |
| 2026-07-01 | The R4 plan was refined to match the standing workflow: commit and push every milestone with detailed commit messages. |
| 2026-07-01 | R4 kickoff docs indexes were synced and verified with `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` -> `3 passed`. |
| 2026-07-01 | Task 2 completed. `tests/course/test_markdown_python_blocks.py` now covers setup material plus Parts 1-4 chapter/lab/solution files. The first TDD run exposed one R2 L3 lab self-check that depended on learner-created variables; it was relabeled as a text self-check template while the executable reference remains in the solution. |
| 2026-07-01 | Task 3 completed. Chapter 04 now starts from the delegated-review failure story, teaches delegation as role badge + task sheet + budget + receipt trail + unresolved-conflict list, shows delegation flow and budget diagrams, covers `run_task`, `run_many`, context isolation, observed over-budget failures, preflight policy failures, duplicate child IDs, and merge conflict visibility. |
| 2026-07-01 | Task 4 completed. Lab 04 now has L1 Follow, L2 Modify/Break-Fix, and L3 Design exercises with Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct feedback for every tier. |
| 2026-07-01 | Task 5 completed. Solution 04 now provides runnable L1/L2 answers, one valid L3 reference design, required invariants, assert-based self-verification, and forward connections to Part 5 context/timeline panels, Part 7 diagnostics, and Part 3 memory boundaries. |
| 2026-07-01 | Task 6 content-status sync started. Course README, docs README, roadmap, execution roadmap, redesign README, and overall progress now describe Part 4 as R4 rewritten material while keeping Phase R4 final verification in progress. |
| 2026-07-01 | Task 6 completed. Docs freshness passed after course/docs index sync, and stale Part 4 status language was removed from the indexed surfaces. |

## Verification Target

Run from `redesign/` unless noted:

```bash
codegraph status .
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

## Verification Results

Run from `redesign/` unless noted.

| Check | Result |
| --- | --- |
| `codegraph status .` on 2026-07-01 | Up to date; 65 files, 1,001 nodes, 2,751 edges. |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` on 2026-07-01 | `3 passed` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` on 2026-07-01 | `4 passed` |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks ... --project-root .` for setup and Parts 1-4 on 2026-07-01 | Checked 95 Python blocks in 15 files; 15 expected outputs matched. |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/04-multi-agent-delegation.md --project-root .` on 2026-07-01 | Checked 12 Python blocks; 9 expected outputs matched. |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/labs/04-delegation-runtime-lab.md --project-root .` on 2026-07-01 | Checked 14 Python blocks; 8 expected outputs matched. |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/solutions/04-delegation-runtime-solution.md --project-root .` on 2026-07-01 | Checked 12 Python blocks; no expected output text fences. |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` after Task 6 on 2026-07-01 | `3 passed` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` after Task 6 on 2026-07-01 | `4 passed` |

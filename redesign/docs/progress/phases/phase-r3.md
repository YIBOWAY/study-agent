# Phase R3 Progress: Course Teaching Redesign - Part 3

Status: Active

Started: 2026-07-01
Completed: TBD
Branch: `codex/redesign-course-r3`

## Goal

Rewrite Part 3 so Memory and Skills teach persistent memory policies and progressive-disclosure skill loading through the local paper research assistant's repeated-session problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phase R1 is complete and established the project-driven course format.
- Phase R2 is complete and established the Part 2 evidence-chain teaching pattern.
- Phase R3 starts from `docs/plans/2026-07-01-phase-r3-course-teaching-redesign.md`.
- `codegraph status .` in `redesign/` reports the existing index is up to date with 65 files, 1,001 nodes, and 2,751 edges, so no fresh `codegraph init` is required.
- First-principles review accepted the R3 plan refinements for markdown Python block automation, six `MemoryKind` usage guidance, open-ended L3 solution invariants, explicit recall ordering, balanced Memory/Skills break-fix coverage, and `validate()` short-circuit teaching.

## Planned Deliverables

- R3 executable plan and progress record.
- Markdown Python fenced-block verification gate under `infra/` and `tests/course/`.
- Part 3 chapter rewrite: `course/chapters/03-memory-and-skills.md`.
- Part 3 lab rewrite: `course/labs/03-memory-skill-runtime-lab.md`.
- Part 3 solution rewrite: `course/solutions/03-memory-skill-runtime-solution.md`.
- Course README, roadmap, docs index, and progress sync.
- Final verification, cleanup, and neat-freak docs reconciliation.

## Task Checklist

- [x] Task 1: Start R3 plan and progress.
- [ ] Task 2: Add markdown Python block verification gate.
- [ ] Task 3: Rewrite Chapter 03 as project-driven Part 3 material.
- [ ] Task 4: Rewrite Lab 03 with L1/L2/L3 exercises and feedback loops.
- [ ] Task 5: Rewrite Solution 03 with reference design, invariants, and why-correct explanations.
- [ ] Task 6: Sync course indexes and progress after content lands.
- [ ] Task 7: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [ ] Chapter/Lab/Solution 03 are rewritten around the repeated-session "assistant has no notebook" problem.
- [ ] Part 3 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [ ] Chapter 03 teaches one "when to use" sentence for all six `MemoryKind` values.
- [ ] Chapter/Lab/Solution 03 show deterministic recall ordering as `(pinned_rank, -score, index)`.
- [ ] Lab 03 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [ ] L3 solution provides one reference design plus required invariants rather than a fake single canonical answer.
- [ ] Memory and Skills both receive Break/Fix coverage, including `validate()` short-circuit order and skill reference path failures.
- [ ] Changed Part 3 fenced Python blocks are covered by `tests/course/test_markdown_python_blocks.py`.
- [ ] Docs index, course roadmap, course README, and overall progress are synced.
- [ ] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R3 started after first-principles review of the R3 plan, current Part 3 material, and the real `MemoryEngine` / `SkillRuntime` code. Codegraph is initialized and up to date, so R3 can use the existing index without re-running `codegraph init`. |
| 2026-07-01 | The R3 plan was refined to accept the six review suggestions: add an automated markdown Python block gate, teach all six `MemoryKind` labels, write L3 as reference design plus invariants, show recall ordering `(pinned_rank, -score, index)`, keep Memory and Skills balanced, and teach `MemoryWritePolicy.validate()` first-error order. |
| 2026-07-01 | R3 kickoff docs indexes were synced and verified with `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` -> `3 passed`. |

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

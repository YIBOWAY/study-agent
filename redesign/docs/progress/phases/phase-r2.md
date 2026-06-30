# Phase R2 Progress: Course Teaching Redesign - Part 2

Status: Complete

Started: 2026-07-01
Completed: 2026-07-01
Branch: `codex/redesign-course-r2`

## Goal

Rewrite Part 2 so Research Core teaches the source -> evidence -> claim -> report chain through the local paper research assistant's citation problem.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Phase R1 is complete and established the project-driven course format.
- Phase R2 starts from the approved teaching redesign spec and the new executable plan `docs/plans/2026-07-01-phase-r2-course-teaching-redesign.md`.
- `codegraph status .` in `redesign/` reports the existing index is up to date with 65 files, 1,001 nodes, and 2,751 edges, so no fresh `codegraph init` is required.

## Planned Deliverables

- R2 executable plan and progress record.
- Part 2 chapter rewrite: `course/chapters/02-research-core-foundations.md`.
- Part 2 lab rewrite: `course/labs/02-source-evidence-claim-lab.md`.
- Part 2 solution rewrite: `course/solutions/02-source-evidence-claim-solution.md`.
- Course README, roadmap, docs index, and progress sync.
- Final verification and cleanup.

## Task Checklist

- [x] Task 1: Start R2 plan and progress.
- [x] Task 2: Rewrite Chapter 02 as project-driven Part 2 material.
- [x] Task 3: Rewrite Lab 02 with L1/L2/L3 exercises and feedback loops.
- [x] Task 4: Rewrite Solution 02 with design rationale and why-correct explanations.
- [x] Task 5: Sync course indexes and progress after content lands.
- [x] Task 6: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [x] Chapter/Lab/Solution 02 are rewritten around the citation problem.
- [x] Part 2 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [x] Lab 02 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback.
- [x] Solution 02 explains what each assertion proves and why the design matters.
- [x] Docs index, course roadmap, course README, and overall progress are synced.
- [x] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R2 started after a first-principles review of `redesign/docs`: Phase R1 was complete, Parts 2-7 were current v1 material, and the next coherent phase was the Part 2 Research Core teaching rewrite. Scope was teaching-layer only; no runtime/product code changes were planned. Codegraph was already initialized and up to date, so direct docs/source reading was sufficient. |
| 2026-07-01 | Task 2 rewrote `course/chapters/02-research-core-foundations.md` as Part 2 Research Core teaching material. The chapter now starts from the citation problem, uses the detective-story evidence-chain framing, adds architecture/data-flow diagrams, teaches `SourceInput -> Source -> Evidence -> Claim -> Report -> ClaimSourceLink`, includes inspect/modify/break/fix loops, and connects link records to Workbench panels. |
| 2026-07-01 | Tasks 3-4 rewrote `course/labs/02-source-evidence-claim-lab.md` and `course/solutions/02-source-evidence-claim-solution.md`. Lab 02 now has L1 Follow, L2 Modify, Break/Fix, and L3 Design exercises with feedback loops. Solution 02 now includes runnable answers, what each assertion proves, and why the evidence-chain design matters for later Memory, Delegation, Workbench, and Production Diagnostics work. |
| 2026-07-01 | Task 5 synced course and docs indexes after Part 2 content landed. `course/README.md`, `redesign/README.md`, `docs/README.md`, `docs/course/roadmap.md`, and `docs/progress/overall.md` now describe Part 2 as R2 rewritten material while keeping Parts 3-7 labeled as current v1 until R3-R7. |
| 2026-07-01 | Task 6 completed final verification and neat-freak docs reconciliation. Fresh verification from `redesign/`: `PYTHONPATH=packages/research_core/src uv run pytest -q` -> `199 passed`; `PYTHONPATH=packages/research_core/src uv run ruff check .` -> `All checks passed!`; `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` -> `3 passed`; `codegraph status .` -> up to date with 65 files, 1,001 nodes, and 2,751 edges; `git diff --check` clean; `cd apps/web && npm ci && npm run build` passed with Vite `46 modules transformed`. Generated `uv.lock`, `.venv`, caches, `node_modules`, `dist`, TypeScript build info, and Python `__pycache__` outputs were removed before final commit. |

## Verification Target

Run from `redesign/` unless noted:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

## Verification Results

Run from `redesign/` unless noted. Results recorded on 2026-07-01.

| Check | Result |
| --- | --- |
| `codegraph status .` | Up to date; 65 files, 1,001 nodes, 2,751 edges. |
| `PYTHONPATH=packages/research_core/src uv run pytest -q` | `199 passed` |
| `PYTHONPATH=packages/research_core/src uv run ruff check .` | `All checks passed!` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` | `3 passed` |
| `git diff --check` | Clean |
| `cd apps/web && npm ci && npm run build` | Passed; Vite built `46 modules transformed`. |
| Neat-freak docs audit | PASS: README, course README, docs index, roadmap, execution roadmap, overall progress, and phase progress are aligned for R2. |

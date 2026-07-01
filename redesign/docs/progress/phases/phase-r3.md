# Phase R3 Progress: Course Teaching Redesign - Part 3

Status: Complete

Started: 2026-07-01
Completed: 2026-07-01
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
- [x] Task 2: Add markdown Python block verification gate.
- [x] Task 3: Rewrite Chapter 03 as project-driven Part 3 material.
- [x] Task 4: Rewrite Lab 03 with L1/L2/L3 exercises and feedback loops.
- [x] Task 5: Rewrite Solution 03 with reference design, invariants, and why-correct explanations.
- [x] Task 6: Sync course indexes and progress after content lands.
- [x] Task 7: Final verification, cleanup, and neat-freak docs reconciliation.

## Exit Signal

- [x] Chapter/Lab/Solution 03 are rewritten around the repeated-session "assistant has no notebook" problem.
- [x] Part 3 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- [x] Chapter 03 teaches one "when to use" sentence for all six `MemoryKind` values.
- [x] Chapter/Lab/Solution 03 show deterministic recall ordering as `(pinned_rank, -score, index)`.
- [x] Lab 03 includes L1 Follow, L2 Modify, and L3 Design exercises with feedback loops.
- [x] L3 solution provides one reference design plus required invariants rather than a fake single canonical answer.
- [x] Memory and Skills both receive Break/Fix coverage, including `validate()` short-circuit order and skill reference path failures.
- [x] Changed Part 3 fenced Python blocks are covered by `tests/course/test_markdown_python_blocks.py`.
- [x] Docs index, course roadmap, course README, and overall progress are synced.
- [x] Fresh verification results are recorded.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-01 | Phase R3 started after first-principles review of the R3 plan, current Part 3 material, and the real `MemoryEngine` / `SkillRuntime` code. Codegraph is initialized and up to date, so R3 can use the existing index without re-running `codegraph init`. |
| 2026-07-01 | The R3 plan was refined to accept the six review suggestions: add an automated markdown Python block gate, teach all six `MemoryKind` labels, write L3 as reference design plus invariants, show recall ordering `(pinned_rank, -score, index)`, keep Memory and Skills balanced, and teach `MemoryWritePolicy.validate()` first-error order. |
| 2026-07-01 | R3 kickoff docs indexes were synced and verified with `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` -> `3 passed`. |
| 2026-07-01 | Task 2 TDD started. `tests/course/test_markdown_python_blocks.py` now captures the desired gate behavior, and the first run failed as expected with `ModuleNotFoundError: No module named 'infra.markdown_python_blocks'`. |
| 2026-07-01 | Task 2 completed. `infra/markdown_python_blocks.py` now executes fenced Python blocks, shares namespace per markdown file, compares adjacent marked `Expected output:` text fences, exposes a CLI, and checks the Part 3 chapter/lab/solution files in pytest. |
| 2026-07-01 | Task 2 follow-up hardened the markdown fence parser so unlabelled fences do not raise an index error while preserving the R3 gate behavior. |
| 2026-07-01 | Task 3 rewrote `course/chapters/03-memory-and-skills.md` as project-driven Part 3 material. The chapter now starts from the repeated-session "assistant has no notebook" problem, teaches Memory as a notebook and Skills as skill packages, covers all six `MemoryKind` labels, shows recall ordering `(pinned_rank, -score, index)`, balances Memory and Skill Break/Fix cases, and adds the `validate()` short-circuit interpretation point. |
| 2026-07-01 | Task 4 rewrote `course/labs/03-memory-skill-runtime-lab.md` with L1 Follow, L2 Modify, and L3 Design exercises. L2 now includes Memory and Skill Break/Fix checks, and L3 is explicitly graded by invariants rather than a single canonical answer. |
| 2026-07-01 | Task 5 rewrote `course/solutions/03-memory-skill-runtime-solution.md`. The solution now provides runnable L1/L2 answers, one valid L3 reference design, required invariants, explicit failure-output interpretation, and forward connections to Part 4 delegation, Part 5 Workbench panels, and Part 7 diagnostics. |
| 2026-07-01 | Task 6 synced course/docs indexes after Part 3 content was completed. `course/README.md`, `redesign/README.md`, `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/overall.md`, and the execution roadmap now describe Part 3 as R3 rewritten while keeping Parts 4-7 as current v1 material. |
| 2026-07-01 | Task 7 completed final verification, cleanup, and neat-freak docs reconciliation. Final checks from `redesign/`: full pytest `203 passed`; ruff `All checks passed!`; docs freshness `3 passed`; markdown Python block gate `4 passed`; `codegraph status .` up to date with 65 files, 1,001 nodes, and 2,751 edges; `git diff --check` clean; `apps/web` Vite build passed with `46 modules transformed`. |
| 2026-07-01 | Neat-freak reconciliation updated `AGENTS.md` and `infra/local-readiness-checklist.md` so future course markdown example changes explicitly run `tests/course/test_markdown_python_blocks.py`. Generated `.venv`, caches, `uv.lock`, `node_modules`, `dist`, TypeScript build info, and Python `__pycache__` outputs were removed before final status checks. |

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
| `PYTHONPATH=packages/research_core/src uv run ruff check infra/markdown_python_blocks.py tests/course/test_markdown_python_blocks.py` on 2026-07-01 | `All checks passed!` |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/03-memory-and-skills.md --project-root .` on 2026-07-01 | Checked 13 Python blocks; 8 expected outputs matched. |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/labs/03-memory-skill-runtime-lab.md --project-root .` on 2026-07-01 | Checked 11 Python blocks; 5 expected outputs matched. |
| `PYTHONPATH=packages/research_core/src uv run python -m infra.markdown_python_blocks course/solutions/03-memory-skill-runtime-solution.md --project-root .` on 2026-07-01 | Checked 10 Python blocks; no expected output text fences. |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` after Task 6 on 2026-07-01 | `3 passed` |
| `PYTHONPATH=packages/research_core/src uv run pytest -q` final on 2026-07-01 | `203 passed` |
| `PYTHONPATH=packages/research_core/src uv run ruff check .` final on 2026-07-01 | `All checks passed!` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` final on 2026-07-01 | `3 passed` |
| `PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` final on 2026-07-01 | `4 passed` |
| `git diff --check` final on 2026-07-01 | Clean |
| `cd apps/web && npm ci && npm run build` final on 2026-07-01 | Passed; Vite built `46 modules transformed`. |
| Neat-freak docs audit on 2026-07-01 | PASS: README, course README, AGENTS, local readiness checklist, docs index, roadmap, execution roadmap, overall progress, and phase progress are aligned for R3. |

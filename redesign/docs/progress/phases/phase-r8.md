# Phase R8 Progress: Course Teaching Redesign - Capstone

Status: Complete

Started: 2026-07-10
Completed: 2026-07-10
Branch: `codex/redesign-course-r7` (R8 work continued on the R7 teaching branch because sandbox blocked creating `codex/redesign-course-r8`)

## Goal

Build the full Capstone under `course/capstone/`: paper fixtures, starter, solution, rubric, trajectory, report, and reflection, so learners can integrate Parts 1-7 into one offline 本地论文研究助手.

## Start Conditions

- Runtime/product phases 0-7 are complete.
- Teaching redesign phases R1-R7 are complete.
- Capstone existed only as an R1 placeholder README.
- Post-review honesty fixes landed in `36bbf91` (CJK retrieval/memory, role tool filter helper, runtime_decision, Workbench unique ids, course honesty).

## Task Checklist

- [x] Task 1: Start R8 plan and progress.
- [x] Task 2: Paper fixtures, rubric, Capstone README.
- [x] Task 3: Starter skeleton and tests.
- [x] Task 4: Reference solution, trajectory, report, reflection.
- [x] Task 5: Residual optimization (gitignore + index honesty).
- [x] Task 6: Docs sync, verification, mark R8 complete.

## Exit Signal

- [x] Capstone materials are complete and offline-runnable.
- [x] Rubric covers the six success criteria from the teaching redesign spec.
- [x] Solution tests prove evidence chain, memory/skill use, workbench timeline, and production diagnostics/persistence/policy decisions.
- [x] Course/docs/progress indexes no longer call Capstone a placeholder.
- [x] Verification baseline recorded; R9 remains planned.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-10 | Phase R8 started. Plan written at `docs/plans/2026-07-10-phase-r8-course-teaching-redesign.md`. Capstone still placeholder at start. |
| 2026-07-10 | Landed paper fixtures, rubric, Capstone README, citation-check skill package. |
| 2026-07-10 | Landed starter skeleton + skip-until-implemented tests; solution `run_capstone()`, tests, trajectory, report, reflection. |
| 2026-07-10 | Residual optimization: root `.gitignore` for node_modules/uv.lock/tsbuildinfo/caches; index honesty sweep for Capstone complete language. |
| 2026-07-10 | Docs/progress/course indexes synced; R8 marked complete; R9 remains planned. |
| 2026-07-10 | Post-R8 review + neat-freak: Engineer Track Capstone step; architecture data-model/runtime/overview honesty; Capstone `runtime_decision` exercised in solution/tests. |

## Deliverables

- `course/capstone/README.md` — real product brief (no longer placeholder)
- `course/capstone/rubric.md` — six success criteria + scoring
- `course/capstone/paper_fixtures/` — offline papers.json + README
- `course/capstone/skills/citation-check/` — progressive disclosure skill package
- `course/capstone/starter/` — incomplete skeleton + scaffold tests
- `course/capstone/solution/` — reference agent, tests, trajectory.jsonl, report.md, reflection.md
- `docs/plans/2026-07-10-phase-r8-course-teaching-redesign.md`
- Index sync across course/README, root README, docs/course/roadmap, docs/README, progress overall/README, execution roadmap, teaching redesign status

## Verification Target

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py course/capstone/starter/test_starter.py -q
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

## Verification Results

- Capstone: `2 passed, 1 skipped` (`solution` green; `starter` skip until implemented)
- Full suite under `tests/`: `215 passed`
- `ruff check .`: clean
- Docs freshness + markdown Python blocks: `8 passed`
- Capstone intentionally outside default `testpaths` (module-name isolation for `agent`/`agent_starter`); run Capstone tests explicitly
- R9 remains planned



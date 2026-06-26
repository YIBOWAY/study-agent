# Redesign Overall Progress

Last updated: 2026-06-26

## Current State

- Active branch: `codex/redesign-phase-3`
- Active phase: Phase 3 complete; next phase is Phase 4 - Multi-Agent and Delegation
- Completed phases: 4 of 8
- Current verification baseline: Course beginner-readiness pass on 2026-06-26 passed course snippets, full redesign suite `116 passed`, `ruff check .` clean, and `git diff --check` clean.
- Course documentation now includes a beginner-ready entrypoint, primer/reference pages, Chapter 00, Lab 00, and rewritten Chapter/Lab/Solution 01.

## Phase Index

| Phase | Status | Progress File | Exit Signal |
| --- | --- | --- | --- |
| Phase 0: Redesign Scaffold | Complete | `phases/phase-0.md` | Scaffold, runtime contracts, fake model baseline, docs, and tests landed. |
| Phase 1: Agent Kernel Course Spine | Complete | `phases/phase-1.md` | Agent runner, tool runtime, context builder, trajectory tests, and first course spine. |
| Phase 2: Research Core | Complete | `phases/phase-2.md` | Research entities, fake retrieval, source ingestion, claim-source mapping, docs, and tests. |
| Phase 3: Memory and Skills | Complete | `phases/phase-3.md` | Memory engine, skill runtime, memory/skill eval cases, and event enum alignment. |
| Phase 4: Multi-Agent and Delegation | Pending | `phases/phase-4.md` | Delegation runtime, isolated child contexts, budget accounting, and merge contract. |
| Phase 5: Workbench Product | Pending | `phases/phase-5.md` | FastAPI API, React workbench, and runtime event surfaces. |
| Phase 6: Framework Comparisons | Pending | `phases/phase-6.md` | Handwritten runner compared against selected frameworks on common tasks. |
| Phase 7: Production Readiness | Pending | `phases/phase-7.md` | Observability, persistence hardening, policy docs, deployment docs, and freshness checks. |

## Update Checklist

- Update the active phase file after each merged task or committed milestone.
- Update this file after each phase start, phase completion, or verification baseline change.
- Keep `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md` aligned with this dashboard.

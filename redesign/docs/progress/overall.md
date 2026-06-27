# Redesign Overall Progress

Last updated: 2026-06-27

## Current State

- Active branch: `codex/redesign-phase-6`
- Active phase: Phase 6 - Framework Comparisons.
- Completed phases: 6 of 8
- Current verification baseline: Phase 6 start on 2026-06-27 from the Phase 5 completion baseline: full redesign suite `173 passed`, `ruff check .` clean, and `apps/web` Vite build clean with `46 modules transformed`.
- Course documentation now includes a beginner-ready entrypoint, primer/reference pages, and Chapter/Lab/Solution 00-05 covering scaffold, Agent Kernel, Research Core, Memory and Skills, Multi-Agent Delegation, and Workbench Product.

## Phase Index

| Phase | Status | Progress File | Exit Signal |
| --- | --- | --- | --- |
| Phase 0: Redesign Scaffold | Complete | `phases/phase-0.md` | Scaffold, runtime contracts, fake model baseline, docs, and tests landed. |
| Phase 1: Agent Kernel Course Spine | Complete | `phases/phase-1.md` | Agent runner, tool runtime, context builder, trajectory tests, and first course spine. |
| Phase 2: Research Core | Complete | `phases/phase-2.md` | Research entities, fake retrieval, source ingestion, claim-source mapping, docs, and tests. |
| Phase 3: Memory and Skills | Complete | `phases/phase-3.md` | Memory engine, skill runtime, memory/skill eval cases, and event enum alignment. |
| Phase 4: Multi-Agent and Delegation | Complete | `phases/phase-4.md` | Delegation runtime, isolated child contexts, budget accounting, merge contract, and A2A stub. |
| Phase 5: Workbench Product | Complete | `phases/phase-5.md` | Workbench snapshot contracts, FastAPI API, React workbench, Course 05, docs sync, and final verification landed. |
| Phase 6: Framework Comparisons | In Progress | `phases/phase-6.md` | Handwritten runner compared against selected frameworks on common tasks. |
| Phase 7: Production Readiness | Pending | `phases/phase-7.md` | Observability, persistence hardening, policy docs, deployment docs, and freshness checks. |

## Update Checklist

- Update the active phase file after each merged task or committed milestone.
- Update this file after each phase start, phase completion, or verification baseline change.
- Keep `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md` aligned with this dashboard.

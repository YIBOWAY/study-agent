# Redesign Overall Progress

Last updated: 2026-07-01

## Current State

- Active branch: `codex/redesign-course-r1`
- Active phase: None. Phase R1 is complete; Phase R2 should start from a new approved plan when the Part 2 teaching rewrite begins.
- Completed runtime/product phases: 8 of 8
- Course teaching redesign: Phase R1 complete; R2-R9 planned.
- Current verification baseline: Phase R1 completion on 2026-07-01: `codegraph status .` up to date with 65 files, 1,001 nodes, and 2,751 edges; full redesign suite `199 passed`; `ruff check .` clean; docs freshness `3 passed`; `apps/web` Vite build clean with `46 modules transformed`; `git diff --check` clean.
- Course documentation now has a complete v1 baseline and a project-driven R1 learner entrypoint. Phase R1 completed the learner guide, roadmap, Part 1 chapters/lab/solution, reusable Part template, and Capstone placeholder for the 本地论文研究助手 narrative. Parts 2-7 remain current v1 material until R2-R7 rewrites land.

## Phase Index

| Phase | Status | Progress File | Exit Signal |
| --- | --- | --- | --- |
| Phase 0: Redesign Scaffold | Complete | `phases/phase-0.md` | Scaffold, runtime contracts, fake model baseline, docs, and tests landed. |
| Phase 1: Agent Kernel Course Spine | Complete | `phases/phase-1.md` | Agent runner, tool runtime, context builder, trajectory tests, and first course spine. |
| Phase 2: Research Core | Complete | `phases/phase-2.md` | Research entities, fake retrieval, source ingestion, claim-source mapping, docs, and tests. |
| Phase 3: Memory and Skills | Complete | `phases/phase-3.md` | Memory engine, skill runtime, memory/skill eval cases, and event enum alignment. |
| Phase 4: Multi-Agent and Delegation | Complete | `phases/phase-4.md` | Delegation runtime, isolated child contexts, budget accounting, merge contract, and A2A stub. |
| Phase 5: Workbench Product | Complete | `phases/phase-5.md` | Workbench snapshot contracts, FastAPI API, React workbench, Course 05, docs sync, and final verification landed. |
| Phase 6: Framework Comparisons | Complete | `phases/phase-6.md` | Offline comparison harness, handwritten runner baseline, framework profiles, recommendation reports, Course 06, docs sync, and final verification landed. |
| Phase 7: Production Readiness | Complete | `phases/phase-7.md` | Offline production-readiness contracts, docs freshness gate, local readiness docs, Course 07, docs sync, and final verification landed. |
| Phase R1: Course Teaching Redesign - Part 1 | Complete | `phases/phase-r1.md` | Learner entrypoint, Part 1 teaching materials, roadmap/template/index, Capstone placeholder, docs sync, subagent reviews, and final verification landed. |

## Update Checklist

- Update the active phase file after each merged task or committed milestone.
- Update this file after each phase start, phase completion, or verification baseline change.
- Keep `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md` aligned with this dashboard.

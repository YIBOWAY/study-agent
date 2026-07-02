# Redesign Overall Progress

Last updated: 2026-07-02

## Current State

- Active branch: `codex/redesign-course-r6`
- Active phase: None. Phase R6 is complete; the R7 teaching-rewrite plan is saved and Phase R7 should start from that approved plan when the Part 7 rewrite begins.
- Completed runtime/product phases: 8 of 8
- Course teaching redesign: Phase R1, R2, R3, R4, R5, and R6 complete; R7 plan saved; R8-R9 planned.
- Current verification baseline: Post-audit R6/R7-planning sync on 2026-07-02: full redesign suite `204 passed`; `ruff check .` clean; docs freshness `3 passed`; markdown Python block gate `5 passed` (covering Parts 0-6); direct Part 7 v1 gate checked 18 Python blocks; `apps/web` Vite build clean; `git diff --check` clean.
- Course documentation now has a complete v1 baseline plus project-driven R1, R2, R3, R4, R5, and R6 teaching material. Phase R1 completed the learner guide, roadmap, Part 1 chapters/lab/solution, reusable Part template, and Capstone placeholder for the 本地论文研究助手 narrative. Phase R2 completed the Part 2 Research Core chapter/lab/solution rewrite around the citation problem. Phase R3 completed the Part 3 Memory and Skills chapter/lab/solution rewrite around the repeated-session notebook problem. Phase R4 completed the Part 4 Multi-Agent Delegation chapter/lab/solution rewrite around delegated-review isolation, budgets, event trails, and unresolved conflicts. Phase R5 completed the Part 5 Workbench Product chapter/lab/solution rewrite around the product-adapter boundary (`from_*` adapters, `summary_row()` projections, `WorkbenchSnapshot` referential-integrity validation, and the downward-only core -> FastAPI -> React boundary), and extended the markdown gate to run `apps/api/src` blocks and cover Part 5. Phase R6 completed the Part 6 Framework Comparisons chapter/lab/solution rewrite around the build-vs-adopt decision made transparent (a pinned task/fixture/metric plus a reproducible weighted score, the `>=0.8` strengths / `<0.55` tradeoffs derivation, and the deterministic tie-break), and brought Part 6 into the markdown gate with no gate helper change. The R7 plan is saved at `docs/plans/2026-07-02-phase-r7-course-teaching-redesign.md`; Part 7 remains current v1 material until that rewrite lands.

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
| Phase R2: Course Teaching Redesign - Part 2 | Complete | `phases/phase-r2.md` | Part 2 Research Core chapter/lab/solution, docs sync, final verification, cleanup, and neat-freak reconciliation landed. |
| Phase R3: Course Teaching Redesign - Part 3 | Complete | `phases/phase-r3.md` | Part 3 Memory and Skills chapter/lab/solution, markdown Python block gate, docs sync, final verification, cleanup, and neat-freak reconciliation landed. |
| Phase R4: Course Teaching Redesign - Part 4 | Complete | `phases/phase-r4.md` | Part 4 Multi-Agent Delegation chapter/lab/solution, markdown Python block gate expansion to Parts 1-4, docs sync, final verification, cleanup, and neat-freak reconciliation landed. |
| Phase R5: Course Teaching Redesign - Part 5 | Complete | `phases/phase-r5.md` | Part 5 Workbench Product chapter/lab/solution rewrite around the product-adapter boundary, markdown gate `apps/api/src` path support plus Part 5 coverage, docs sync, final verification, and whole-branch review landed. |
| Phase R6: Course Teaching Redesign - Part 6 | Complete | `phases/phase-r6.md` | Part 6 Framework Comparisons chapter/lab/solution rewrite around the build-vs-adopt decision with transparent weighted scoring, Part 6 gate coverage (no helper change), docs sync, final verification, and whole-branch review landed. |

## Update Checklist

- Update the active phase file after each merged task or committed milestone.
- Update this file after each phase start, phase completion, or verification baseline change.
- Keep `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md` aligned with this dashboard.

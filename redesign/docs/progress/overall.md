# Redesign Overall Progress

Last updated: 2026-07-10

## Current State

- Active branch: `codex/redesign-course-r7` (R1–R9 teaching work + F0–F2 framework tracks)
- Active phase: None.
- Completed runtime/product phases: 8 of 8
- Course teaching redesign: Phase R1, R2, R3, R4, R5, R6, R7, R8, and R9 complete.
- Parallel framework tracks: Phase F0, F1, and F2 complete. F3–F5 planned (LC Parts 5–7 + Capstone, then LG).
- Current verification baseline: post-F2 pass on 2026-07-10: full redesign suite offline green; `packages/langchain_course/tests` unit green with integration skip unless `RUN_DEEPSEEK_TESTS=1`; `ruff check .` clean; docs freshness green. DeepSeek keys via env or gitignored `.env`.
- Course documentation now has a complete v1 baseline plus project-driven R1–R9 teaching material. Phase R1–R9 delivered handwritten 本地论文研究助手 course through Capstone and reference materials. Phase F0 scaffolded parallel LangChain/LangGraph teaching tracks. Phase F1 delivered LangChain Parts 1–2 (inspectable `bind_tools` agent loop + local keyword evidence chain). Phase F2 delivered LangChain Parts 3–4 (offline memory notebook + progressive skills + multi-worker delegation budgets/merge) with chapters/labs/solutions.

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
| Phase R7: Course Teaching Redesign - Part 7 | Complete | `phases/phase-r7.md` | Part 7 Production Readiness chapter/lab/solution rewrite, Part 7 markdown gate coverage, docs sync, final verification, cleanup, neat-freak reconciliation, and whole-branch review landed. |
| Phase R8: Course Teaching Redesign - Capstone | Complete | `phases/phase-r8.md` | Full Capstone materials under course/capstone/; indexes synced. |
| Phase R9: Course Teaching Redesign - Reference & Support | Complete | `phases/phase-r9.md` | Reference materials (patterns, troubleshooting, DD index, discussion answers, glossary); indexes synced. |
| Phase F0: LangChain / LangGraph Parallel Track Scaffold | Complete | `phases/phase-f0.md` | Track dirs, teaching packages, optional deps, DeepSeek hello, indexes; no Parts 1–7 content. |
| Phase F1: LangChain Parts 1–2 | Complete | `phases/phase-f1.md` | `.env` loading; tool-calling agent kernel; evidence chain; chapters/labs/solutions. |
| Phase F2: LangChain Parts 3–4 | Complete | `phases/phase-f2.md` | Memory notebook + skill loader; multi-worker delegation budgets/merge; chapters/labs/solutions. |
| Phase F3: LangChain Parts 5–7 + Capstone | Planned | — | Workbench, comparisons, production, LC Capstone. |
| Phase F4–F5: LangGraph full mirror | Planned | — | LG Parts 1–7 + Capstone after LC. |

## Update Checklist

- Update the active phase file after each merged task or committed milestone.
- Update this file after each phase start, phase completion, or verification baseline change.
- Keep `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md` aligned with this dashboard.

## Phase R8

Status: Complete (2026-07-10).

Delivered full Capstone materials under `course/capstone/`: paper fixtures, rubric, starter, solution, trajectory, report, reflection. Course and docs indexes no longer treat Capstone as a placeholder.

Progress: [phases/phase-r8.md](phases/phase-r8.md)

## Phase R9

Status: Complete (2026-07-10).

Delivered reference and support materials under `course/reference/`: common patterns, troubleshooting, design-decision index, discussion prompts with detailed 参考答案与解析, and glossary expansion for Parts 1–7 + Capstone. Course and docs indexes no longer list R9 as planned-only.

Progress: [phases/phase-r9.md](phases/phase-r9.md)

## Phase F0

Status: Complete (2026-07-10).

Scaffolded parallel LangChain/LangGraph teaching tracks: `course/tracks/{langchain,langgraph}/`, packages `langchain_course` / `langgraph_course`, optional uv groups, DeepSeek config + hello lab, indexes. Does not replace R1–R9.

Progress: [phases/phase-f0.md](phases/phase-f0.md)

## Phase F1

Status: Complete (2026-07-10).

LangChain Parts 1–2: `.env` DeepSeek loading, `run_tool_calling_agent` with inspectable steps, local `PaperDoc` / `KeywordRetriever` / `build_claim_links`, track chapters/labs/solutions, handwritten mapping. Main CI remains offline without key.

Progress: [phases/phase-f1.md](phases/phase-f1.md)

## Phase F2

Status: Complete (2026-07-10).

LangChain Parts 3–4: offline `Notebook` / `SkillLoader`, `DelegationCoordinator` with budgets and merge conflicts, track chapters/labs/solutions 03–04, handwritten mapping extended. Main CI remains offline without key.

Progress: [phases/phase-f2.md](phases/phase-f2.md)

# Course Roadmap

This roadmap turns the comprehensive redesign spec and the course teaching redesign spec into a learner-facing course map. Executable phase plans live under `docs/plans/`; this file explains how those phases become teachable material.

## Course Promise

The course should teach Agent engineering through a single, growing project: a 本地论文研究助手 (local paper research assistant). Every Part adds a capability to this assistant. All examples run offline with FakeModel and static paper fixtures. The event trail is the primary learning tool — learners inspect it, break it, and fix it.

## Tracks

### Beginner Track

For learners who know some Python but are new to Agent engineering, the path is Part-based. Parts 1-7 build on each other and end with the Capstone; do not treat later Parts as independent one-off chapters.

R1 completed the teaching-redesign pass for the learner entrypoint and Part 1. R2 completed the Part 2 Research Core rewrite. R3 completed the Part 3 Memory and Skills rewrite. R4 completed the Part 4 Multi-Agent Delegation content rewrite. R5 completed the Part 5 Workbench Product rewrite. R6 completed the Part 6 Framework Comparisons rewrite. R7 completed the Part 7 Production Readiness rewrite. R8 completed the full Capstone materials under `course/capstone/`. R9 completed the reference and support materials under `course/reference/`.

| Step | File to read/do | What capability the assistant gains |
|------|-----------------|--------------------------------------|
| 0 | Read [course/README.md](../../course/README.md), [python-terminal-primer.md](../../course/reference/python-terminal-primer.md), and [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md).<br>Do [00-environment-check.md](../../course/labs/00-environment-check.md), then compare with [00-environment-check-solution.md](../../course/solutions/00-environment-check-solution.md). | The learner gets the offline setup and vocabulary. The assistant has not gained a runtime capability yet. |
| 1 | Read Part 1 Section 1 in [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md), then Sections 2-5 in [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md).<br>Do [01-agent-runner-lab.md](../../course/labs/01-agent-runner-lab.md), then compare with [01-agent-runner-solution.md](../../course/solutions/01-agent-runner-solution.md). | Part 1: Agent Kernel — the assistant gains the smallest think-act-observe loop and an inspectable event trail. This is the completed R1 rewrite material. |
| 2 | Read [02-research-core-foundations.md](../../course/chapters/02-research-core-foundations.md).<br>Do [02-source-evidence-claim-lab.md](../../course/labs/02-source-evidence-claim-lab.md), then compare with [02-source-evidence-claim-solution.md](../../course/solutions/02-source-evidence-claim-solution.md). | Part 2: Research Core — the assistant gains a source -> evidence -> claim -> report evidence chain. This is the R2 rewritten material. |
| 3 | Read [03-memory-and-skills.md](../../course/chapters/03-memory-and-skills.md).<br>Do [03-memory-skill-runtime-lab.md](../../course/labs/03-memory-skill-runtime-lab.md), then compare with [03-memory-skill-runtime-solution.md](../../course/solutions/03-memory-skill-runtime-solution.md). | Part 3: Memory and Skills — the assistant gains a memory notebook, write/recall policies, skill package manifests, and progressive disclosure. This is the R3 rewritten material. |
| 4 | Read [04-multi-agent-delegation.md](../../course/chapters/04-multi-agent-delegation.md).<br>Do [04-delegation-runtime-lab.md](../../course/labs/04-delegation-runtime-lab.md), then compare with [04-delegation-runtime-solution.md](../../course/solutions/04-delegation-runtime-solution.md). | Part 4: Multi-Agent Delegation — the assistant gains child context isolation, budget accounting, parent delegation event trails, and unresolved-conflict visibility. This is the R4 rewritten material. |
| 5 | Read [05-workbench-product.md](../../course/chapters/05-workbench-product.md).<br>Do [05-workbench-product-lab.md](../../course/labs/05-workbench-product-lab.md), then compare with [05-workbench-product-solution.md](../../course/solutions/05-workbench-product-solution.md). | Part 5: Workbench Product — the assistant gains a product adapter, FastAPI read API, and React workbench. This is the R5 rewritten material. |
| 6 | Read [06-framework-comparisons.md](../../course/chapters/06-framework-comparisons.md).<br>Do [06-framework-comparisons-lab.md](../../course/labs/06-framework-comparisons-lab.md), then compare with [06-framework-comparisons-solution.md](../../course/solutions/06-framework-comparisons-solution.md). | Part 6: Framework Comparisons — the learner gains a method for a defensible build-vs-adopt decision using a pinned task/fixture/metric and a transparent weighted score. This is the R6 rewritten material. |
| 7 | Read [07-production-readiness.md](../../course/chapters/07-production-readiness.md).<br>Do [07-production-readiness-lab.md](../../course/labs/07-production-readiness-lab.md), then compare with [07-production-readiness-solution.md](../../course/solutions/07-production-readiness-solution.md). | Part 7: Production Readiness — the assistant gains diagnostics, JSONL event replay, approval policy, sandbox policy, and docs freshness as local-first production boundaries. This is the R7 rewritten material. |
| 8 | Read [course/capstone/README.md](../../course/capstone/README.md) and [course/capstone/rubric.md](../../course/capstone/rubric.md). Fill [course/capstone/starter/](../../course/capstone/starter/), then compare with [course/capstone/solution/](../../course/capstone/solution/). | Capstone — the learner integrates all Parts into a complete 本地论文研究助手. This is the completed R8 Capstone material. |

### Engineer Track

For readers already comfortable with Python projects, pytest, and basic Agent terminology:

1. Skim [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md).
2. Skim [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md) for the Part 1 narrative and mental model, then start the build loop at [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md).
3. Continue through Part 2, Part 3, Part 4, Part 5, Part 6, and Part 7 as R2/R3/R4/R5/R6/R7 rewritten material.
4. Read [07-production-readiness.md](../../course/chapters/07-production-readiness.md) when evaluating local-first production-readiness contracts.
5. Use labs and solutions as runnable verification material.
6. Finish with Capstone: read [course/capstone/README.md](../../course/capstone/README.md) and [rubric.md](../../course/capstone/rubric.md), fill [starter/](../../course/capstone/starter/), then compare with [solution/](../../course/capstone/solution/).

## Shape

The target course shape is:

1. Part 1: Agent Kernel — the smallest think-act-observe loop, with event trail
2. Part 2: Research Core — source -> evidence -> claim -> report evidence chain
3. Part 3: Memory and Skills — persistent memory policies and skill loading
4. Part 4: Multi-Agent Delegation — child context isolation and budget accounting
5. Part 5: Workbench Product — product adapter, FastAPI API, React workbench
6. Part 6: Framework Comparisons — method for comparing frameworks on the same task
7. Part 7: Production Readiness — diagnostics, persistence, approval, and sandbox policies
8. Capstone — integrate all Parts into a complete 本地论文研究助手

R1 makes this shape visible and rewrites Part 1. R2 rewrites Part 2. R3 rewrites Part 3. R4 rewrites Part 4. R5 rewrites Part 5. R6 rewrites Part 6. R7 rewrites Part 7. R8 builds the full Capstone. R9 adds support/reference material (complete).

## Part Contract

Every rewritten Part should include:

- at least 1 full Build -> Inspect -> Break -> Fix -> Reflect cycle,
- 3-tier exercises with feedback: L1 Follow, L2 Modify, and L3 Design,
- feedback for each exercise covering common errors, failure-output interpretation, where to go back, and why the correct answer is correct,
- 2+ ASCII diagrams, such as architecture maps, object relationship diagrams, event timelines, or data-flow diagrams,
- 3+ callouts using the stable ASCII tags `[DD]`, `[TRAP]`, `[CHECK]`, `[BIG]`, or `[DEEP]`,
- an eval gate with concrete commands or checks,
- reflection questions that ask the learner to explain tradeoffs, not just recall names.

Parts 2-7 now follow this contract after R2/R3/R4/R5/R6/R7. Capstone is complete after R8. Support/reference materials are complete after R9.

## Current Materials

Parts 1-7, Capstone, and R9 reference materials are current teaching materials.
"Current" means the path is present and linked from the course map.

- [2026-06-25-study-agent-comprehensive-redesign.md](../specs/2026-06-25-study-agent-comprehensive-redesign.md): approved redesign spec for the broader runtime/product/course direction.
- [2026-06-30-course-teaching-redesign.md](../specs/2026-06-30-course-teaching-redesign.md): approved teaching-redesign spec for the project-driven course and R1-R9 plan.
- [2026-06-30-phase-r1-course-teaching-redesign.md](../plans/2026-06-30-phase-r1-course-teaching-redesign.md): completed R1 implementation plan.
- [2026-07-01-phase-r2-course-teaching-redesign.md](../plans/2026-07-01-phase-r2-course-teaching-redesign.md): completed R2 implementation plan.
- [2026-07-01-phase-r3-course-teaching-redesign.md](../plans/2026-07-01-phase-r3-course-teaching-redesign.md): completed R3 implementation plan.
- [2026-07-01-phase-r4-course-teaching-redesign.md](../plans/2026-07-01-phase-r4-course-teaching-redesign.md): completed R4 implementation plan.
- [2026-07-01-phase-r5-course-teaching-redesign.md](../plans/2026-07-01-phase-r5-course-teaching-redesign.md): completed R5 implementation plan.
- [2026-07-01-phase-r6-course-teaching-redesign.md](../plans/2026-07-01-phase-r6-course-teaching-redesign.md): completed R6 implementation plan.
- [2026-07-02-phase-r7-course-teaching-redesign.md](../plans/2026-07-02-phase-r7-course-teaching-redesign.md): completed R7 implementation plan for the Part 7 Production Readiness teaching rewrite.
- [2026-07-10-phase-r8-course-teaching-redesign.md](../plans/2026-07-10-phase-r8-course-teaching-redesign.md): completed R8 implementation plan for the full Capstone project.
- [2026-07-10-phase-r9-course-teaching-redesign.md](../plans/2026-07-10-phase-r9-course-teaching-redesign.md): completed R9 implementation plan for reference and support materials.
- [2026-07-10-langchain-langgraph-parallel-tracks-design.md](../specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md): design for parallel LC/LG full-mirror tracks.
- [2026-07-10-phase-f0-langchain-langgraph-scaffold.md](../plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md): F0 scaffold plan (packages, DeepSeek hello, indexes).
- [2026-07-10-phase-f1-langchain-parts-1-2.md](../plans/2026-07-10-phase-f1-langchain-parts-1-2.md): F1 LangChain Parts 1–2 plan.
- [2026-07-10-phase-f2-langchain-parts-3-4.md](../plans/2026-07-10-phase-f2-langchain-parts-3-4.md): F2 LangChain Parts 3–4 plan.
- [2026-07-10-phase-f3-langchain-parts-5-7-capstone.md](../plans/2026-07-10-phase-f3-langchain-parts-5-7-capstone.md): F3 LangChain Parts 5–7 + Capstone plan.
- [course/tracks/langchain/README.md](../../course/tracks/langchain/README.md): LangChain parallel track entry (F0–F3).
- [course/tracks/langchain/chapters/01-agent-kernel-langchain.md](../../course/tracks/langchain/chapters/01-agent-kernel-langchain.md): LC Part 1 chapter.
- [course/tracks/langchain/chapters/02-research-core-langchain.md](../../course/tracks/langchain/chapters/02-research-core-langchain.md): LC Part 2 chapter.
- [course/tracks/langchain/chapters/03-memory-skills-langchain.md](../../course/tracks/langchain/chapters/03-memory-skills-langchain.md): LC Part 3 chapter.
- [course/tracks/langchain/chapters/04-delegation-langchain.md](../../course/tracks/langchain/chapters/04-delegation-langchain.md): LC Part 4 chapter.
- [course/tracks/langchain/chapters/05-workbench-langchain.md](../../course/tracks/langchain/chapters/05-workbench-langchain.md): LC Part 5 chapter.
- [course/tracks/langchain/chapters/06-comparisons-langchain.md](../../course/tracks/langchain/chapters/06-comparisons-langchain.md): LC Part 6 chapter.
- [course/tracks/langchain/chapters/07-production-langchain.md](../../course/tracks/langchain/chapters/07-production-langchain.md): LC Part 7 chapter.
- [course/tracks/langchain/capstone/README.md](../../course/tracks/langchain/capstone/README.md): LC Capstone.
- [course/tracks/langgraph/README.md](../../course/tracks/langgraph/README.md): LangGraph parallel track entry (placeholder until F4).
- [course/README.md](../../course/README.md): learner entrypoint, track selection, commands, and common stuck points.
- [python-terminal-primer.md](../../course/reference/python-terminal-primer.md): minimal terminal and Python concepts needed for the course.
- [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md): plain-language Agent kernel vocabulary (Parts 1–7 + Capstone).
- [common-patterns.md](../../course/reference/common-patterns.md): reusable agent engineering patterns with honesty boundaries.
- [troubleshooting.md](../../course/reference/troubleshooting.md): common errors and fix guidance.
- [design-decisions-index.md](../../course/reference/design-decisions-index.md): index of all `[DD]` / `[TRAP]` callouts.
- [discussion-prompts.md](../../course/reference/discussion-prompts.md): per-part discussion prompts with detailed answers and analysis.
- Setup material: [00-environment-check.md](../../course/labs/00-environment-check.md), [00-environment-check-solution.md](../../course/solutions/00-environment-check-solution.md).
- Part 1 / R1 completed material: [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md), [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md), [01-agent-runner-lab.md](../../course/labs/01-agent-runner-lab.md), [01-agent-runner-solution.md](../../course/solutions/01-agent-runner-solution.md).
- Part 2 / R2 completed material: [02-research-core-foundations.md](../../course/chapters/02-research-core-foundations.md), [02-source-evidence-claim-lab.md](../../course/labs/02-source-evidence-claim-lab.md), [02-source-evidence-claim-solution.md](../../course/solutions/02-source-evidence-claim-solution.md).
- Part 3 / R3 completed material: [03-memory-and-skills.md](../../course/chapters/03-memory-and-skills.md), [03-memory-skill-runtime-lab.md](../../course/labs/03-memory-skill-runtime-lab.md), [03-memory-skill-runtime-solution.md](../../course/solutions/03-memory-skill-runtime-solution.md).
- Part 4 / R4 completed material: [04-multi-agent-delegation.md](../../course/chapters/04-multi-agent-delegation.md), [04-delegation-runtime-lab.md](../../course/labs/04-delegation-runtime-lab.md), [04-delegation-runtime-solution.md](../../course/solutions/04-delegation-runtime-solution.md).
- Part 5 / R5 completed material: [05-workbench-product.md](../../course/chapters/05-workbench-product.md), [05-workbench-product-lab.md](../../course/labs/05-workbench-product-lab.md), [05-workbench-product-solution.md](../../course/solutions/05-workbench-product-solution.md).
- Part 6 / R6 completed material: [06-framework-comparisons.md](../../course/chapters/06-framework-comparisons.md), [06-framework-comparisons-lab.md](../../course/labs/06-framework-comparisons-lab.md), [06-framework-comparisons-solution.md](../../course/solutions/06-framework-comparisons-solution.md).
- Part 7 / R7 rewritten material: [07-production-readiness.md](../../course/chapters/07-production-readiness.md), [07-production-readiness-lab.md](../../course/labs/07-production-readiness-lab.md), [07-production-readiness-solution.md](../../course/solutions/07-production-readiness-solution.md).
- [course/capstone/README.md](../../course/capstone/README.md): completed R8 Capstone brief.
- [course/capstone/rubric.md](../../course/capstone/rubric.md): Capstone success criteria and scoring.
- [course/capstone/starter/](../../course/capstone/starter/): starter skeleton and scaffold tests.
- [course/capstone/solution/](../../course/capstone/solution/): reference solution, tests, trajectory, report, reflection.
- [echo-tool-task.md](../../course/framework_comparisons/reports/echo-tool-task.md): shared echo-tool task report.
- [recommendation-matrix.md](../../course/framework_comparisons/reports/recommendation-matrix.md): current recommendation matrix report.

## Near-Term Course Work

- Phase R1 (complete): restructured the learner entrypoint and Part 1 around the 本地论文研究助手 narrative, added the Part contract, updated the roadmap/template/index, and added the Capstone placeholder.
- Phase R2 (complete): rewrote Part 2 so Research Core teaches the source -> evidence -> claim -> report chain through the assistant's citation problem.
- Phase R3 (complete): rewrote Part 3 so Memory and Skills teach persistent memory policies and skill loading through repeated research sessions, plus added markdown Python block verification for changed course examples.
- Phase R4 (complete): rewrote Part 4 so Multi-Agent Delegation teaches child context isolation, budget accounting, parent event trails, and unresolved-conflict visibility through divided research work.
- Phase R5 (complete): rewrote Part 5 so Workbench Product teaches the product adapter, FastAPI read API, and React workbench through the researcher-facing inspectable-snapshot problem, and brought Part 5 into the markdown Python block gate.
- Phase R6 (complete): rewrote Part 6 so Framework Comparisons teaches a defensible build-vs-adopt decision through a pinned task/fixture/metric and a transparent weighted score, and brought Part 6 into the markdown Python block gate.
- Phase R7 (complete): rewrote Part 7 so Production Readiness teaches diagnostics, persistence, approval, sandbox policies, and docs freshness as local-first deployment boundaries, then brought Part 7 into the markdown Python block gate.
- Phase R8 (complete): built the full Capstone under `course/capstone/`, including paper fixtures, starter, solution, rubric, event trail, report, and reflection.
- Phase R9 (complete): added reference and support materials — common patterns, troubleshooting, design-decision index, discussion prompts with detailed answers, and glossary updates.
- Phase F0 (complete): scaffold parallel LangChain/LangGraph tracks under `course/tracks/`, teaching packages, DeepSeek hello, optional deps — does not replace R1–R9.
- Phase F1 (complete): LangChain Parts 1–2 (tool-calling agent + evidence chain), `.env` loading, track chapters/labs/solutions.
- Phase F2 (complete): LangChain Parts 3–4 (memory/skills notebook + multi-worker delegation), offline unit tests, track chapters/labs/solutions.
- Phase F3 (complete): LangChain Parts 5–7 + Capstone (workbench snapshot, comparisons, production contracts, offline Capstone).
- Phase F3 (planned): LangChain Parts 5–7 + Capstone.
- Phase F4–F5 (planned): full LangGraph mirror (Parts 1–7 + Capstone) after LC.

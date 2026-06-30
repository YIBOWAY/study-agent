# Course Roadmap

This roadmap turns the comprehensive redesign spec and the course teaching redesign spec into a learner-facing course map. Executable phase plans live under `docs/plans/`; this file explains how those phases become teachable material.

## Course Promise

The course should teach Agent engineering through a single, growing project: a 本地论文研究助手 (local paper research assistant). Every Part adds a capability to this assistant. All examples run offline with FakeModel and static paper fixtures. The event trail is the primary learning tool — learners inspect it, break it, and fix it.

## Tracks

### Beginner Track

For learners who know some Python but are new to Agent engineering, the path is Part-based. Parts 1-7 build on each other and end with the Capstone; do not treat later Parts as independent one-off chapters.

R1 completed the teaching-redesign pass for the learner entrypoint and Part 1. R2 is now rewriting Part 2. Parts 3-7 are still current v1 material until their planned R3-R7 rewrites land.

| Step | File to read/do | What capability the assistant gains |
|------|-----------------|--------------------------------------|
| 0 | Read [course/README.md](../../course/README.md), [python-terminal-primer.md](../../course/reference/python-terminal-primer.md), and [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md).<br>Do [00-environment-check.md](../../course/labs/00-environment-check.md), then compare with [00-environment-check-solution.md](../../course/solutions/00-environment-check-solution.md). | The learner gets the offline setup and vocabulary. The assistant has not gained a runtime capability yet. |
| 1 | Read Part 1 Section 1 in [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md), then Sections 2-5 in [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md).<br>Do [01-agent-runner-lab.md](../../course/labs/01-agent-runner-lab.md), then compare with [01-agent-runner-solution.md](../../course/solutions/01-agent-runner-solution.md). | Part 1: Agent Kernel — the assistant gains the smallest think-act-observe loop and an inspectable event trail. This is the completed R1 rewrite material. |
| 2 | Read [02-research-core-foundations.md](../../course/chapters/02-research-core-foundations.md).<br>Do [02-source-evidence-claim-lab.md](../../course/labs/02-source-evidence-claim-lab.md), then compare with [02-source-evidence-claim-solution.md](../../course/solutions/02-source-evidence-claim-solution.md). | Part 2: Research Core — the assistant gains a source -> evidence -> claim -> report evidence chain. This is currently being rewritten in R2. |
| 3 | Read [03-memory-and-skills.md](../../course/chapters/03-memory-and-skills.md).<br>Do [03-memory-skill-runtime-lab.md](../../course/labs/03-memory-skill-runtime-lab.md), then compare with [03-memory-skill-runtime-solution.md](../../course/solutions/03-memory-skill-runtime-solution.md). | Part 3: Memory and Skills — the assistant gains persistent memory policies and skill loading. This remains current v1 material until the planned R3 rewrite. |
| 4 | Read [04-multi-agent-delegation.md](../../course/chapters/04-multi-agent-delegation.md).<br>Do [04-delegation-runtime-lab.md](../../course/labs/04-delegation-runtime-lab.md), then compare with [04-delegation-runtime-solution.md](../../course/solutions/04-delegation-runtime-solution.md). | Part 4: Multi-Agent Delegation — the assistant gains child context isolation and budget accounting. This remains current v1 material until the planned R4 rewrite. |
| 5 | Read [05-workbench-product.md](../../course/chapters/05-workbench-product.md).<br>Do [05-workbench-product-lab.md](../../course/labs/05-workbench-product-lab.md), then compare with [05-workbench-product-solution.md](../../course/solutions/05-workbench-product-solution.md). | Part 5: Workbench Product — the assistant gains a product adapter, FastAPI API, and React workbench. This remains current v1 material until the planned R5 rewrite. |
| 6 | Read [06-framework-comparisons.md](../../course/chapters/06-framework-comparisons.md).<br>Do [06-framework-comparisons-lab.md](../../course/labs/06-framework-comparisons-lab.md), then compare with [06-framework-comparisons-solution.md](../../course/solutions/06-framework-comparisons-solution.md). | Part 6: Framework Comparisons — the learner gains a method for comparing frameworks on the same task. This remains current v1 material until the planned R6 rewrite. |
| 7 | Read [07-production-readiness.md](../../course/chapters/07-production-readiness.md).<br>Do [07-production-readiness-lab.md](../../course/labs/07-production-readiness-lab.md), then compare with [07-production-readiness-solution.md](../../course/solutions/07-production-readiness-solution.md). | Part 7: Production Readiness — the assistant gains diagnostics, persistence, approval, and sandbox policies. This remains current v1 material until the planned R7 rewrite. |
| 8 | Read [course/capstone/README.md](../../course/capstone/README.md). | Capstone — the learner integrates all Parts into a complete 本地论文研究助手. The current page is a placeholder; the full Capstone is planned for R8. |

### Engineer Track

For readers already comfortable with Python projects, pytest, and basic Agent terminology:

1. Skim [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md).
2. Skim [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md) for the Part 1 narrative and mental model, then start the build loop at [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md).
3. Continue through Parts 2-7 when reading the related source modules, while remembering that Parts 2-7 are current v1 material until R2-R7.
4. Read [07-production-readiness.md](../../course/chapters/07-production-readiness.md) when evaluating production-readiness contracts.
5. Use labs and solutions as runnable verification material.

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

R1 makes this shape visible and rewrites Part 1. R2-R9 are planned follow-up phases, so this target shape should not be read as a claim that every Part already follows the new teaching method.

## Part Contract

Every rewritten Part should include:

- at least 1 full Build -> Inspect -> Break -> Fix -> Reflect cycle,
- 3-tier exercises with feedback: L1 Follow, L2 Modify, and L3 Design,
- feedback for each exercise covering common errors, failure-output interpretation, where to go back, and why the correct answer is correct,
- 2+ ASCII diagrams, such as architecture maps, object relationship diagrams, event timelines, or data-flow diagrams,
- 3+ callouts using the stable ASCII tags `[DD]`, `[TRAP]`, `[CHECK]`, `[BIG]`, or `[DEEP]`,
- an eval gate with concrete commands or checks,
- reflection questions that ask the learner to explain tradeoffs, not just recall names.

Parts 2-7 must satisfy this contract after their R2-R7 rewrites. Until then, they remain valid v1 learning material, not finished examples of the new Part contract.

## Current Materials

Current means the file exists in the tree now. It does not mean every file has already been rewritten under the R1 teaching method.

- [2026-06-25-study-agent-comprehensive-redesign.md](../specs/2026-06-25-study-agent-comprehensive-redesign.md): approved redesign spec for the broader runtime/product/course direction.
- [2026-06-30-course-teaching-redesign.md](../specs/2026-06-30-course-teaching-redesign.md): approved teaching-redesign spec for the project-driven course and R1-R9 plan.
- [2026-06-30-phase-r1-course-teaching-redesign.md](../plans/2026-06-30-phase-r1-course-teaching-redesign.md): completed R1 implementation plan.
- [2026-07-01-phase-r2-course-teaching-redesign.md](../plans/2026-07-01-phase-r2-course-teaching-redesign.md): active R2 implementation plan.
- [course/README.md](../../course/README.md): learner entrypoint, track selection, commands, and common stuck points.
- [python-terminal-primer.md](../../course/reference/python-terminal-primer.md): minimal terminal and Python concepts needed for the course.
- [agent-kernel-glossary.md](../../course/reference/agent-kernel-glossary.md): plain-language Agent kernel vocabulary.
- Setup material: [00-environment-check.md](../../course/labs/00-environment-check.md), [00-environment-check-solution.md](../../course/solutions/00-environment-check-solution.md).
- Part 1 / R1 completed material: [00-before-agent-kernel.md](../../course/chapters/00-before-agent-kernel.md), [01-agent-kernel-foundations.md](../../course/chapters/01-agent-kernel-foundations.md), [01-agent-runner-lab.md](../../course/labs/01-agent-runner-lab.md), [01-agent-runner-solution.md](../../course/solutions/01-agent-runner-solution.md).
- Part 2 material currently being rewritten in R2: [02-research-core-foundations.md](../../course/chapters/02-research-core-foundations.md), [02-source-evidence-claim-lab.md](../../course/labs/02-source-evidence-claim-lab.md), [02-source-evidence-claim-solution.md](../../course/solutions/02-source-evidence-claim-solution.md).
- Part 3 current v1 material: [03-memory-and-skills.md](../../course/chapters/03-memory-and-skills.md), [03-memory-skill-runtime-lab.md](../../course/labs/03-memory-skill-runtime-lab.md), [03-memory-skill-runtime-solution.md](../../course/solutions/03-memory-skill-runtime-solution.md).
- Part 4 current v1 material: [04-multi-agent-delegation.md](../../course/chapters/04-multi-agent-delegation.md), [04-delegation-runtime-lab.md](../../course/labs/04-delegation-runtime-lab.md), [04-delegation-runtime-solution.md](../../course/solutions/04-delegation-runtime-solution.md).
- Part 5 current v1 material: [05-workbench-product.md](../../course/chapters/05-workbench-product.md), [05-workbench-product-lab.md](../../course/labs/05-workbench-product-lab.md), [05-workbench-product-solution.md](../../course/solutions/05-workbench-product-solution.md).
- Part 6 current v1 material: [06-framework-comparisons.md](../../course/chapters/06-framework-comparisons.md), [06-framework-comparisons-lab.md](../../course/labs/06-framework-comparisons-lab.md), [06-framework-comparisons-solution.md](../../course/solutions/06-framework-comparisons-solution.md).
- Part 7 current v1 material: [07-production-readiness.md](../../course/chapters/07-production-readiness.md), [07-production-readiness-lab.md](../../course/labs/07-production-readiness-lab.md), [07-production-readiness-solution.md](../../course/solutions/07-production-readiness-solution.md).
- [course/capstone/README.md](../../course/capstone/README.md): current Capstone placeholder; full Capstone project material is planned for R8.
- [echo-tool-task.md](../../course/framework_comparisons/reports/echo-tool-task.md): shared echo-tool task report.
- [recommendation-matrix.md](../../course/framework_comparisons/reports/recommendation-matrix.md): current recommendation matrix report.

## Near-Term Course Work

- Phase R1 (complete): restructured the learner entrypoint and Part 1 around the 本地论文研究助手 narrative, added the Part contract, updated the roadmap/template/index, and added the Capstone placeholder.
- Phase R2 (in progress): rewrite Part 2 so Research Core teaches the source -> evidence -> claim -> report chain through the assistant's citation problem.
- Phase R3 (planned): rewrite Part 3 so Memory and Skills teach persistent memory policies and skill loading through repeated research sessions.
- Phase R4 (planned): rewrite Part 4 so Multi-Agent Delegation teaches child context isolation and budget accounting through divided research work.
- Phase R5 (planned): rewrite Part 5 so Workbench Product teaches the product adapter, FastAPI API, and React workbench through a researcher-facing interface.
- Phase R6 (planned): rewrite Part 6 so Framework Comparisons teach how to compare frameworks on the same task without moving framework code into the product runtime.
- Phase R7 (planned): rewrite Part 7 so Production Readiness teaches diagnostics, persistence, approval, and sandbox policies as local-first deployment boundaries.
- Phase R8 (planned): build the full Capstone under `course/capstone/`, including paper fixtures, starter, solution, rubric, event trail, report, and reflection.
- Phase R9 (planned): add reference and support materials such as common patterns, troubleshooting, design-decision index, discussion prompts, and glossary updates.

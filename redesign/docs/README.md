# Study Agent Redesign Docs

This directory is the canonical archive for the redesign version of the project.

## Structure

- `specs/`: approved design documents.
- `plans/`: executable phase plans.
- `progress/`: total and per-phase progress records.
- `architecture/`: stable architecture notes.
- `course/`: course roadmap and chapter authoring template.
- `operations/`: production-readiness and local deployment notes.
- `glossary.md`: redesign terminology.

## Document Index

- `specs/2026-06-25-study-agent-comprehensive-redesign.md`: comprehensive redesign spec.
- `specs/2026-06-30-course-teaching-redesign.md`: project-driven teaching redesign for the 本地论文研究助手 course.
- `plans/2026-06-25-redesign-execution-roadmap.md`: phase index and sequencing.
- `plans/2026-06-25-phase-0-redesign-scaffold.md`: first executable implementation plan.
- `plans/2026-06-25-phase-1-agent-kernel-course-spine.md`: Agent Kernel course spine implementation plan.
- `plans/2026-06-25-phase-2-research-core.md`: Research Core implementation plan.
- `plans/2026-06-26-phase-3-memory-and-skills.md`: Memory and Skills implementation plan.
- `plans/2026-06-26-phase-4-multi-agent-delegation.md`: Multi-Agent and Delegation implementation plan.
- `plans/2026-06-26-phase-5-workbench-product.md`: Workbench Product implementation plan.
- `plans/2026-06-27-phase-6-framework-comparisons.md`: Framework Comparisons implementation plan.
- `plans/2026-06-30-phase-7-production-readiness.md`: Production Readiness implementation plan.
- `plans/2026-06-30-phase-r1-course-teaching-redesign.md`: Phase R1 implementation plan for the learner entrypoint and Part 1 teaching rewrite.
- `plans/2026-07-01-phase-r2-course-teaching-redesign.md`: Phase R2 implementation plan for the Part 2 Research Core teaching rewrite.
- `plans/2026-07-01-phase-r3-course-teaching-redesign.md`: Phase R3 implementation plan for the Part 3 Memory and Skills teaching rewrite.
- `plans/2026-07-01-phase-r4-course-teaching-redesign.md`: Phase R4 implementation plan for the Part 4 Multi-Agent Delegation teaching rewrite.
- `progress/overall.md`: phase status dashboard for humans and agents.
- `architecture/overview.md`: double-layer repository and dependency direction.
- `architecture/runtime.md`: runtime contracts, Phase 1 agent loop, fake provider boundary, delegation events, and Phase 5 product boundary.
- `architecture/data-model.md`: research entities, memory records, skill package model, delegation contracts, workbench snapshot model, fake retrieval, ingestion, and claim-source mapping.
- `course/roadmap.md`: project-driven Part roadmap and current rewrite status for the 本地论文研究助手 course.
- `course/chapter-template.md`: reusable project-driven Part authoring template with Build -> Inspect -> Break -> Fix -> Reflect structure.
- `product/workbench.md`: product boundary and first workbench screen expectations.
- `operations/production-readiness.md`: local production-readiness boundary and verification notes.
- `../infra/local-readiness-checklist.md`: local milestone verification and cleanup checklist.
- `adr/README.md`: architecture decision record folder and format.
- `living-landscape.md`: dated framework/protocol landscape notes.
- `glossary.md`: core redesign vocabulary, including Workbench Product terms.

## Course Index

- `../course/README.md`: project-driven learner entrypoint for building the 本地论文研究助手.
- `../course/capstone/README.md`: Capstone placeholder; full offline project materials are planned for R8.
- `../course/reference/python-terminal-primer.md`: terminal and Python primer for course readers.
- `../course/reference/agent-kernel-glossary.md`: plain-language Agent kernel glossary.
- `../course/chapters/00-before-agent-kernel.md`: Part 1 Section 1 mental model and narrative start.
- `../course/labs/00-environment-check.md`: local environment readiness lab.
- `../course/solutions/00-environment-check-solution.md`: expected environment-check outputs.
- `../course/chapters/01-agent-kernel-foundations.md`: Part 1 Sections 2-5 build, inspect, break, fix, and gate loop.
- `../course/labs/01-agent-runner-lab.md`: Part 1 L1/L2/L3 AgentRunner practice with feedback loops.
- `../course/solutions/01-agent-runner-solution.md`: Part 1 L1/L2/L3 rationale and why-correct explanations.
- `../course/chapters/02-research-core-foundations.md`: Part 2 R2 Research Core evidence-chain material.
- `../course/labs/02-source-evidence-claim-lab.md`: Part 2 R2 Source/Evidence/Claim lab with L1/L2/L3 exercises.
- `../course/solutions/02-source-evidence-claim-solution.md`: Part 2 R2 Research Core solution with design rationale.
- `../course/chapters/03-memory-and-skills.md`: Part 3 R3 Memory notebook and Skill package material.
- `../course/labs/03-memory-skill-runtime-lab.md`: Part 3 R3 Memory/Skill lab with L1/L2/L3 exercises.
- `../course/solutions/03-memory-skill-runtime-solution.md`: Part 3 R3 Memory/Skill solution with reference design and invariants.
- `../course/chapters/04-multi-agent-delegation.md`: Part 4 current v1 Multi-Agent Delegation material while R4 is active.
- `../course/labs/04-delegation-runtime-lab.md`: Part 4 current v1 DelegationRuntime lab while R4 is active.
- `../course/solutions/04-delegation-runtime-solution.md`: Part 4 current v1 DelegationRuntime solution while R4 is active.
- `../course/chapters/05-workbench-product.md`: Part 5 current v1 Workbench Product integration material until R5.
- `../course/labs/05-workbench-product-lab.md`: Part 5 current v1 WorkbenchSnapshot, API, and web build lab until R5.
- `../course/solutions/05-workbench-product-solution.md`: Part 5 current v1 Workbench Product solution until R5.
- `../course/chapters/06-framework-comparisons.md`: Part 6 current v1 framework comparison method material until R6.
- `../course/labs/06-framework-comparisons-lab.md`: Part 6 current v1 recommendation matrix lab until R6.
- `../course/solutions/06-framework-comparisons-solution.md`: Part 6 current v1 Framework Comparisons solution until R6.
- `../course/chapters/07-production-readiness.md`: Part 7 current v1 production-readiness contracts material until R7.
- `../course/labs/07-production-readiness-lab.md`: Part 7 current v1 production diagnostics, persistence, approval, and sandbox lab until R7.
- `../course/solutions/07-production-readiness-solution.md`: Part 7 current v1 Production Readiness solution until R7.
- `../course/framework_comparisons/reports/echo-tool-task.md`: shared echo-tool task report.
- `../course/framework_comparisons/reports/recommendation-matrix.md`: current framework recommendation matrix.

## Rule

New redesign specs and plans should be stored here instead of the legacy `docs/superpowers/` tree, so the redesign version remains self-contained.

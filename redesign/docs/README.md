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
- `plans/2026-06-25-redesign-execution-roadmap.md`: phase index and sequencing.
- `plans/2026-06-25-phase-0-redesign-scaffold.md`: first executable implementation plan.
- `plans/2026-06-25-phase-1-agent-kernel-course-spine.md`: Agent Kernel course spine implementation plan.
- `plans/2026-06-25-phase-2-research-core.md`: Research Core implementation plan.
- `plans/2026-06-26-phase-3-memory-and-skills.md`: Memory and Skills implementation plan.
- `plans/2026-06-26-phase-4-multi-agent-delegation.md`: Multi-Agent and Delegation implementation plan.
- `plans/2026-06-26-phase-5-workbench-product.md`: Workbench Product implementation plan.
- `plans/2026-06-27-phase-6-framework-comparisons.md`: Framework Comparisons implementation plan.
- `plans/2026-06-30-phase-7-production-readiness.md`: Production Readiness implementation plan.
- `progress/overall.md`: phase status dashboard for humans and agents.
- `architecture/overview.md`: double-layer repository and dependency direction.
- `architecture/runtime.md`: runtime contracts, Phase 1 agent loop, fake provider boundary, delegation events, and Phase 5 product boundary.
- `architecture/data-model.md`: research entities, memory records, skill package model, delegation contracts, workbench snapshot model, fake retrieval, ingestion, and claim-source mapping.
- `course/roadmap.md`: 24-week course domain map and current chapter index.
- `course/chapter-template.md`: beginner-ready structure for future full course chapters.
- `product/workbench.md`: product boundary and first workbench screen expectations.
- `operations/production-readiness.md`: local production-readiness boundary and verification notes.
- `../infra/local-readiness-checklist.md`: local milestone verification and cleanup checklist.
- `adr/README.md`: architecture decision record folder and format.
- `living-landscape.md`: dated framework/protocol landscape notes.
- `glossary.md`: core redesign vocabulary, including Workbench Product terms.

## Course Index

- `../course/README.md`: learner entrypoint, track selection, commands, and common stuck points.
- `../course/reference/python-terminal-primer.md`: terminal and Python primer for course readers.
- `../course/reference/agent-kernel-glossary.md`: plain-language Agent kernel glossary.
- `../course/chapters/00-before-agent-kernel.md`: pre-kernel mental model.
- `../course/labs/00-environment-check.md`: local environment readiness lab.
- `../course/solutions/00-environment-check-solution.md`: expected environment-check outputs.
- `../course/chapters/01-agent-kernel-foundations.md`: first-principles Agent Kernel chapter.
- `../course/labs/01-agent-runner-lab.md`: hands-on AgentRunner lab.
- `../course/solutions/01-agent-runner-solution.md`: expected lab solution.
- `../course/chapters/02-research-core-foundations.md`: Research Core evidence-chain chapter.
- `../course/labs/02-source-evidence-claim-lab.md`: Source/Evidence/Claim lab.
- `../course/solutions/02-source-evidence-claim-solution.md`: expected Research Core lab solution.
- `../course/chapters/03-memory-and-skills.md`: Memory policy and SkillRuntime chapter.
- `../course/labs/03-memory-skill-runtime-lab.md`: Memory/Skill lab.
- `../course/solutions/03-memory-skill-runtime-solution.md`: expected Memory/Skill lab solution.
- `../course/chapters/04-multi-agent-delegation.md`: Multi-Agent Delegation chapter.
- `../course/labs/04-delegation-runtime-lab.md`: DelegationRuntime lab.
- `../course/solutions/04-delegation-runtime-solution.md`: expected DelegationRuntime lab solution.
- `../course/chapters/05-workbench-product.md`: Workbench Product integration chapter.
- `../course/labs/05-workbench-product-lab.md`: WorkbenchSnapshot, API, and web build lab.
- `../course/solutions/05-workbench-product-solution.md`: expected Workbench Product lab solution.
- `../course/chapters/06-framework-comparisons.md`: framework comparison method chapter.
- `../course/labs/06-framework-comparisons-lab.md`: recommendation matrix lab.
- `../course/solutions/06-framework-comparisons-solution.md`: expected Framework Comparisons lab solution.
- `../course/chapters/07-production-readiness.md`: production-readiness contracts chapter.
- `../course/labs/07-production-readiness-lab.md`: production diagnostics, persistence, approval, and sandbox lab.
- `../course/solutions/07-production-readiness-solution.md`: expected Production Readiness lab solution.
- `../course/framework_comparisons/reports/echo-tool-task.md`: shared echo-tool task report.
- `../course/framework_comparisons/reports/recommendation-matrix.md`: current framework recommendation matrix.

## Rule

New redesign specs and plans should be stored here instead of the legacy `docs/superpowers/` tree, so the redesign version remains self-contained.

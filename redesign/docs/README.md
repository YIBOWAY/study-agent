# Study Agent Redesign Docs

This directory is the canonical archive for the redesign version of the project.

## Structure

- `specs/`: approved design documents.
- `plans/`: executable phase plans.
- `progress/`: total and per-phase progress records.
- `architecture/`: stable architecture notes.
- `glossary.md`: redesign terminology.

## Document Index

- `specs/2026-06-25-study-agent-comprehensive-redesign.md`: comprehensive redesign spec.
- `plans/2026-06-25-redesign-execution-roadmap.md`: phase index and sequencing.
- `plans/2026-06-25-phase-0-redesign-scaffold.md`: first executable implementation plan.
- `plans/2026-06-25-phase-1-agent-kernel-course-spine.md`: Agent Kernel course spine implementation plan.
- `plans/2026-06-25-phase-2-research-core.md`: Research Core implementation plan.
- `plans/2026-06-26-phase-3-memory-and-skills.md`: Memory and Skills implementation plan.
- `progress/overall.md`: phase status dashboard for humans and agents.
- `architecture/overview.md`: double-layer repository and dependency direction.
- `architecture/runtime.md`: runtime contracts, Phase 1 agent loop, and fake provider boundary.
- `architecture/data-model.md`: research entities, memory records, skill package model, fake retrieval, ingestion, and claim-source mapping.
- `course/roadmap.md`: 24-week course domain map and current chapter index.
- `course/chapter-template.md`: required structure for future full course chapters.
- `product/workbench.md`: product boundary and first workbench screen expectations.
- `adr/README.md`: architecture decision record folder and format.
- `living-landscape.md`: dated framework/protocol landscape notes.
- `glossary.md`: core redesign vocabulary.

## Course Index

- `../course/chapters/01-agent-kernel-foundations.md`: first-principles Agent Kernel chapter.
- `../course/labs/01-agent-runner-lab.md`: hands-on AgentRunner lab.
- `../course/solutions/01-agent-runner-solution.md`: expected lab solution.

## Rule

New redesign specs and plans should be stored here instead of the legacy `docs/superpowers/` tree, so the redesign version remains self-contained.

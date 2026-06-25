# Research Agent Workbench

The Workbench is the final product surface for the redesign. It is not a landing
page and not a chat-only demo. The first screen should be an operational research
workspace.

## Product Boundary

The Workbench helps a user move from a research question to a grounded report:

- create or select a project,
- start a research run,
- inspect the run timeline,
- review sources and evidence,
- inspect agent state, memory, skills, and evals,
- edit or export the final report.

## Primary Screens

- Workspace navigation
- Task composer
- Run timeline
- Agent inspector
- Source and evidence panel
- Report editor
- Memory panel
- Skill panel
- Eval panel
- Delegation tree after the multi-agent phase lands

## Runtime Dependencies

The web product must depend on API contracts and product adapters, not directly
on provider SDKs. Shared behavior belongs in `packages/research_core`; product
transport belongs in `apps/api`; product UI belongs in `apps/web`.

## Not In Scope For V1

- enterprise multi-tenant auth,
- billing,
- mobile app,
- browser extension,
- unrestricted code execution,
- full model fine-tuning.

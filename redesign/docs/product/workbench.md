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

Phase 5 implements the first local product slice. It is intentionally read-only
and deterministic: the API returns a demo `WorkbenchSnapshot` record, and the web
UI renders that record without requiring model credentials, a database, or
network retrieval.

## Phase 5 Data Contract

The product adapter lives in `packages/research_core/src/research_core/product`.
Its main contract is `WorkbenchSnapshot.to_record()`, which returns a plain
JSON-compatible record with:

- `project`
- `run`
- `timeline`
- `delegation`
- `sources`
- `report`
- `memory`
- `skills`
- `evals`

This record is not raw runtime state. It is a product-shaped snapshot that
combines runtime events, research evidence, report links, memory rows, skill
rows, eval rows, and delegation nodes into the shape the API and UI need.

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

Phase 5 renders all of these as first-screen panels in `apps/web`.

## API Surface

The FastAPI app lives in `apps/api/src/research_api/main.py`.

Current read endpoints:

- `GET /health`
- `GET /api/workbench/snapshot`
- `GET /api/workbench/timeline`

The API must remain a transport layer. It should call product contracts and
return JSON records; it should not become the home for research logic, provider
calls, or UI-only data transformations.

## Runtime Dependencies

The web product must depend on API contracts and product adapters, not directly
on provider SDKs. Shared behavior belongs in `packages/research_core`; product
transport belongs in `apps/api`; product UI belongs in `apps/web`.

`apps/web` fetches `/api/workbench/snapshot` and falls back to a deterministic
local fixture with the same TypeScript `WorkbenchSnapshot` shape. The fallback is
for offline development and browser verification; it is not a separate product
data model.

## Not In Scope For V1

- enterprise multi-tenant auth,
- billing,
- mobile app,
- browser extension,
- unrestricted code execution,
- full model fine-tuning.

Also deferred after Phase 5:

- persistence and migrations,
- editing APIs and report export,
- SSE/websocket timeline streaming,
- real retrieval/provider adapters,
- async delegation execution.

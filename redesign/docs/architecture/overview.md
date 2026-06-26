# Architecture Overview

## Shape

The redesign uses a double-layer repository under `redesign/`:

- `course/`: learning chapters, labs, solutions, and framework comparisons.
- `apps/`: product applications.
- `packages/`: shared runtime packages.
- `evals/`: datasets, trajectory fixtures, and evaluation reports.
- `docs/`: architecture, specs, plans, and glossary.
- `infra/`: deployment and operations placeholders for deployment phases.

The two product-facing layers are the course/labs layer and the workbench product
layer. `packages/research_core` is the shared core that keeps those layers aligned
without making either one depend on the other's implementation details.

## Dependency Direction

`packages/research_core` is the center:

- `apps/api` may depend on `research_core`.
- `apps/web` may depend on API contracts generated from or aligned with `apps/api`.
- `course` may use `research_core` contracts for product integration labs.
- `research_core` must not depend on apps, course chapters, provider SDKs, or databases.

## Current Boundary

Phase 0 only creates:

- runtime message contracts,
- runtime event contracts,
- fake model provider baseline,
- tests,
- docs.

Phase 1 adds:

- local tool runtime contracts,
- deterministic context building,
- the minimal agent runner loop,
- trajectory regression helpers,
- the first Agent Kernel course chapter, lab, and solution.

Phase 2 adds:

- research domain entities,
- deterministic source ingestion,
- fake retrieval for offline tests and future evals,
- claim-source mapping helpers,
- data model docs.

Phase 3 adds:

- deterministic in-process memory records and policies,
- folder-based skill loading with progressive disclosure,
- memory pollution and skill loading eval cases.

Phase 4 adds:

- delegation role, task, budget, result, and merge contracts,
- deterministic `DelegationRuntime` orchestration,
- parent `delegate_start`, `delegate_event`, and `delegate_finish` event records,
- child context isolation and budget accounting eval cases,
- a local `A2AAdapterStub` export boundary without network transport.

Product APIs, web UI, async delegation, real A2A transport, persistence, and real retrieval adapters are introduced by later approved phase plans.

# Study Agent Redesign Execution Roadmap

This roadmap indexes the executable phase plans for the `redesign/` version of the project.

## Planning Rule

Each phase must produce working, testable software or durable documentation. A phase is not complete unless its tests, docs, and verification commands are recorded in its own plan.

## Phase Sequence

### Phase 0: Redesign Scaffold

Plan: `redesign/docs/plans/2026-06-25-phase-0-redesign-scaffold.md`

Purpose:

- Create the self-contained `redesign/` project shell.
- Add the first Python package boundaries.
- Add minimal runtime contracts.
- Add the fake model fixture baseline.
- Add the first offline test baseline.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `redesign/README.md`, `redesign/AGENTS.md`, and architecture docs explain the new boundary.
- Fake search and retrieval fixtures are deferred to Phase 2, where retrieval contracts are introduced.

### Phase 1: Agent Kernel Course Spine

Purpose:

- Implement AgentMessage, RunEvent, AgentRunner, ToolRuntime, and ContextBuilder.
- Add the first course chapters and labs for Agent foundations.
- Add trajectory regression tests.

Plan document should be created after Phase 0 is complete, using the tested Phase 0 file layout.

### Phase 2: Research Core

Purpose:

- Add research domain entities: Project, ResearchRun, Source, Evidence, Claim, Report.
- Add fake retrieval and source ingestion.
- Add claim-source mapping tests.

Plan document should be created after Phase 1 contracts are stable.

### Phase 3: Memory and Skills

Purpose:

- Add MemoryEngine with recall/write policies.
- Add SkillRuntime with folder-based progressive disclosure.
- Add memory pollution and skill loading eval cases.

Plan document should be created after Phase 2 research entities are available.

### Phase 4: Multi-Agent and Delegation

Purpose:

- Add delegation runtime, child context isolation, role policies, budget accounting, and merge contract.
- Add multi-agent eval cases.
- Add an A2A adapter stub.

Plan document should be created after Phase 3 memory and skill policies are stable.

### Phase 5: Workbench Product

Purpose:

- Add FastAPI product API.
- Add React + TypeScript workbench.
- Surface research run timeline, delegation tree, source/evidence panels, memory, skills, and evals.

Plan document should be created after Phase 4 runtime events are stable.

### Phase 6: Framework Comparisons

Purpose:

- Compare handwritten runner against selected frameworks on the same tasks.
- Keep framework code in `course/framework_comparisons/`, not in the product runtime path.

Plan document should be created after Phase 5 has enough product flows to compare against.

### Phase 7: Production Readiness

Purpose:

- Add observability, persistence hardening, approval policy, sandbox policy, deployment docs, and docs freshness checks.

Plan document should be created after Phase 5 and Phase 6 have produced stable runtime and product contracts.

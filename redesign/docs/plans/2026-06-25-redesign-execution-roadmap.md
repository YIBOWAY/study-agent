# Study Agent Redesign Execution Roadmap

This roadmap indexes the executable phase plans for the `redesign/` version of the project.

## Planning Rule

Each phase must produce working, testable software or durable documentation. A phase is not complete unless its tests, docs, and verification commands are recorded in its own plan.

## Progress Rule

Each phase must update `redesign/docs/progress/overall.md` and its matching `redesign/docs/progress/phases/phase-N.md` file when the phase starts, when key tasks land, and when the phase completes.

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
- Fake search and retrieval fixtures were deferred out of Phase 0 and introduced by Phase 2.

### Phase 1: Agent Kernel Course Spine

Plan: `redesign/docs/plans/2026-06-25-phase-1-agent-kernel-course-spine.md`

Purpose:

- Implement AgentMessage, RunEvent, AgentRunner, ToolRuntime, and ContextBuilder.
- Add the first course chapters and labs for Agent foundations.
- Add trajectory regression tests.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `docs/architecture/runtime.md` explains the Phase 1 loop.
- `docs/glossary.md` defines ToolRuntime, ContextBuilder, AgentRunner, and Trajectory Regression.
- `course/chapters/01-agent-kernel-foundations.md`, `course/labs/01-agent-runner-lab.md`, and `course/solutions/01-agent-runner-solution.md` exist.

### Phase 2: Research Core

Plan: `redesign/docs/plans/2026-06-25-phase-2-research-core.md`

Purpose:

- Add research domain entities: Project, ResearchRun, Source, Evidence, Claim, Report.
- Add fake retrieval and source ingestion.
- Add claim-source mapping tests.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `docs/architecture/data-model.md` explains Project, ResearchRun, Source, Evidence, Claim, Report, fake retrieval, ingestion, and claim-source mapping.
- `docs/glossary.md` defines the Phase 2 research concepts.
- Claim-source mapping rejects missing evidence and missing source references.

Follow-up:

- Research planning and report synthesis remain part of the larger Research Core
  milestone from the comprehensive spec, but they are intentionally deferred to
  the Knowledge and Deep Research slice after memory and skills policies exist.
  They should not be treated as delivered by Phase 2's entity/retrieval contract
  work.

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

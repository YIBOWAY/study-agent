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
- `course/README.md`, beginner reference pages, Chapter 00, Lab 00, Chapter 01, Lab 01, and solutions exist.

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

Plan: `redesign/docs/plans/2026-06-26-phase-3-memory-and-skills.md`

Purpose:

- Add MemoryEngine with recall/write policies.
- Add SkillRuntime with folder-based progressive disclosure.
- Add memory pollution and skill loading eval cases.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `MemoryEngine` supports deterministic recall/write policy tests.
- `SkillRuntime` loads `SKILL.md` before explicitly reading references.
- Memory pollution and skill loading eval cases pass.

Follow-up:

- Persistent memory, memory conflict resolution, skill execution steps, MCP, and
  product memory/skill panels are deferred to later phases.

### Phase 4: Multi-Agent and Delegation

Plan: `redesign/docs/plans/2026-06-26-phase-4-multi-agent-delegation.md`

Purpose:

- Add delegation runtime, child context isolation, role policies, budget accounting, and merge contract.
- Add multi-agent eval cases.
- Add an A2A adapter stub.

Exit criteria:

- `cd redesign && uv run pytest -q` passes. Completed on 2026-06-26 with `152 passed`; post-audit course/test catch-up raised the current baseline to `160 passed`.
- `cd redesign && uv run ruff check .` passes. Completed on 2026-06-26 with `All checks passed!`.
- `DelegationRuntime` emits `delegate_start`, `delegate_event`, and `delegate_finish`. Completed.
- Child contexts are isolated from parent history. Completed.
- Budget accounting and merge eval cases pass. Completed.
- `A2AAdapterStub` serializes delegation tasks and rejects remote sends with an explicit not-implemented error. Completed.

Follow-up:

- True async execution, cancellation propagation, remote A2A transport, and product delegation-tree UI are deferred to later phases.

### Phase 5: Workbench Product

Plan: `redesign/docs/plans/2026-06-26-phase-5-workbench-product.md`

Purpose:

- Add FastAPI product API.
- Add React + TypeScript workbench.
- Surface research run timeline, delegation tree, source/evidence panels, memory, skills, and evals.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `cd redesign/apps/web && npm run build` passes.
- Workbench snapshot contracts cover project, run, timeline, delegation, sources, report, memory, skills, and eval panels.
- FastAPI exposes health, snapshot, and timeline endpoints.
- React first screen is an operational workbench, not a landing page.
- Course Chapter/Lab/Solution 05 teaches the product integration layer.

### Phase 6: Framework Comparisons

Plan: `redesign/docs/plans/2026-06-27-phase-6-framework-comparisons.md`

Purpose:

- Compare handwritten runner against selected frameworks on the same tasks.
- Keep framework code in `course/framework_comparisons/`, not in the product runtime path.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `cd redesign/apps/web && npm run build` passes.
- Shared comparison tasks, handwritten runner baseline, framework profiles, recommendation matrix, and comparison reports live under `course/framework_comparisons/`.
- Course Chapter/Lab/Solution 06 teaches the comparison workflow.

### Phase 7: Production Readiness

Plan: `redesign/docs/plans/2026-06-30-phase-7-production-readiness.md`

Purpose:

- Add observability, persistence hardening, approval policy, sandbox policy, deployment docs, and docs freshness checks.

Exit criteria:

- `cd redesign && uv run pytest -q` passes.
- `cd redesign && uv run ruff check .` passes.
- `cd redesign/apps/web && npm install && npm run build` passes.
- Production-readiness contracts remain offline-first and independent from real
  cloud, auth, database, provider, or network transport dependencies.
- Docs freshness checks validate course/docs index paths.
- Course Chapter/Lab/Solution 07 teaches production readiness as inspectable
  contracts.

### Phase R1: Course Teaching Redesign - Part 1

Plan: `redesign/docs/plans/2026-06-30-phase-r1-course-teaching-redesign.md`

Purpose:

- Reframe the learner entrypoint around a single project: a 本地论文研究助手.
- Rewrite Part 1 so Chapter 00, Chapter 01, Lab 01, and Solution 01 teach the Agent Kernel through plain-language mental models, event-trail inspection, break/fix loops, three-tier exercises, and design rationale.
- Add the reusable Part teaching template, project-driven roadmap, and Capstone placeholder.

Exit criteria:

- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes with `199 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes.
- `cd redesign/apps/web && npm ci && npm run build` passes.
- Independent subagent reviews pass for spec/progress consistency and beginner teaching quality.

Follow-up:

- R2, R3, and R4 completed the Part 2, Part 3, and Part 4 teaching rewrites; R5-R7 should rewrite Parts 5-7 with the same project-driven teaching method.
- R8 should build the full Capstone materials under `course/capstone/`.
- R9 should add support references such as troubleshooting, design-decision indexes, discussion prompts, and glossary updates.

### Phase R2: Course Teaching Redesign - Part 2

Plan: `redesign/docs/plans/2026-07-01-phase-r2-course-teaching-redesign.md`

Purpose:

- Rewrite Part 2 so Research Core starts from the local paper research assistant's citation problem.
- Teach `SourceInput`, `SourceIngestor`, `FakeRetriever`, `Evidence`, `Claim`, `Report`, and `ClaimSourceLink` through a source -> evidence -> claim -> report data flow.
- Add L1/L2/L3 lab exercises with feedback loops and a solution that explains why the assertions prove the evidence chain.

Exit criteria:

- Chapter/Lab/Solution 02 are rewritten using the R1 teaching contract. Completed on 2026-07-01.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 2 as R2 rewritten. Completed on 2026-07-01.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes. Completed on 2026-07-01 with `199 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes. Completed on 2026-07-01 with `All checks passed!`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes. Completed on 2026-07-01 with `3 passed`.
- `cd redesign/apps/web && npm ci && npm run build` passes. Completed on 2026-07-01 with Vite `46 modules transformed`.

Follow-up:

- R3 rewrote Part 3 with the same project-driven teaching method while keeping Part 2 as the evidence-chain foundation.

### Phase R3: Course Teaching Redesign - Part 3

Plan: `redesign/docs/plans/2026-07-01-phase-r3-course-teaching-redesign.md`

Purpose:

- Rewrite Part 3 so Memory and Skills start from the local paper research assistant's repeated-session problem.
- Teach `MemoryRecord`, `MemoryKind`, `MemoryWritePolicy`, `MemoryRecallPolicy`, `MemoryEngine`, `SkillPackage`, and `SkillRuntime` through notebook and skill-package mental models.
- Add a markdown Python block verification gate so changed course examples run against the real local API instead of relying only on manual copy/paste checks.

Exit criteria:

- Chapter/Lab/Solution 03 are rewritten using the R1/R2 teaching contract. Completed on 2026-07-01.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 3 as R3 rewritten. Completed on 2026-07-01.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes. Completed on 2026-07-01 with `203 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes. Completed on 2026-07-01 with `All checks passed!`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes. Completed on 2026-07-01 with `3 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passes. Completed on 2026-07-01 with `4 passed`.
- `cd redesign/apps/web && npm ci && npm run build` passes. Completed on 2026-07-01 with Vite `46 modules transformed`.

Follow-up:

- R4 content has landed to rewrite Part 4 with the same project-driven teaching method while keeping Part 3 as the memory/skill boundary foundation.

### Phase R4: Course Teaching Redesign - Part 4

Plan: `redesign/docs/plans/2026-07-01-phase-r4-course-teaching-redesign.md`

Purpose:

- Rewrite Part 4 so Multi-Agent Delegation starts from the local paper research assistant's delegated-review problem.
- Teach `AgentRolePolicy`, `DelegationTask`, `DelegationBudget`, `DelegationRuntime`, `DelegationResult`, and `DelegationMergeResult` through child context isolation, parent event trails, step-budget accounting, and unresolved-conflict visibility.
- Backfill the markdown Python block gate so Parts 1-4 course examples are checked against the real local API.

Exit criteria:

- Chapter/Lab/Solution 04 are rewritten using the R1-R3 teaching contract. Completed on 2026-07-01.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 4 as R4 rewritten after content lands. Completed on 2026-07-01.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passes for Parts 1-4.
- `cd redesign/apps/web && npm ci && npm run build` passes.

Completion notes:

- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passed on 2026-07-01 with `203 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passed on 2026-07-01 with `All checks passed!`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passed on 2026-07-01 with `3 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passed on 2026-07-01 with `4 passed`.
- `cd redesign/apps/web && npm ci && npm run build` passed on 2026-07-01 with Vite `46 modules transformed`.

### Phase R5: Course Teaching Redesign - Part 5

Plan: `redesign/docs/plans/2026-07-01-phase-r5-course-teaching-redesign.md`

Status: Complete (2026-07-01).

Purpose:

- Rewrite Part 5 so Workbench Product starts from the local paper research assistant's "give the researcher an inspectable workbench without inventing a separate data model" problem.
- Teach the `research_core.product` `from_*` adapters, `summary_row()` projections, `WorkbenchSnapshot` referential-integrity validation, and the downward-only core -> FastAPI -> React boundary.
- Extend the markdown Python block gate so Part 5 API examples run with `apps/api/src` on the path, then bring Part 5 into the gate.

Exit criteria:

- Chapter/Lab/Solution 05 are rewritten using the R1-R4 teaching contract.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 5 as R5 rewritten after content lands.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passes for Parts 1-5.
- `cd redesign/apps/web && npm ci && npm run build` passes.

Completion notes:

- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passed on 2026-07-01 with `204 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passed on 2026-07-01 with `All checks passed!`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passed on 2026-07-01 with `3 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passed on 2026-07-01 with `5 passed` (Parts 0-5 plus the `apps/api/src` path test).
- `cd redesign/apps/web && npm ci && npm run build` passed on 2026-07-01.

### Phase R6: Course Teaching Redesign - Part 6

Plan: `redesign/docs/plans/2026-07-01-phase-r6-course-teaching-redesign.md`

Status: Complete (2026-07-01).

Purpose:

- Rewrite Part 6 so Framework Comparisons starts from the build-vs-adopt "why not just use LangChain/CrewAI?" decision problem.
- Teach the `course.framework_comparisons` harness through a transparent weighted score: `ComparisonTask` weights x `FrameworkProfile` scores -> `FrameworkRecommendation`, with the `>=0.8` strengths / `<0.55` tradeoffs derivation and the deterministic tie-break.
- Add the three Part 6 files to the markdown Python block gate (no gate helper change is needed; `course.framework_comparisons` already imports under the gate).

Exit criteria:

- Chapter/Lab/Solution 06 are rewritten using the R1-R5 teaching contract.
- `course/README.md`, `README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 6 as R6 rewritten after content lands.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passes for Parts 1-6.
- `cd redesign/apps/web && npm ci && npm run build` passes.

Completion notes:

- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passed on 2026-07-01 with `204 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passed on 2026-07-01 with `All checks passed!`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passed on 2026-07-01 with `3 passed`.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passed on 2026-07-01 with `5 passed` (Parts 0-6).
- `cd redesign/apps/web && npm ci && npm run build` passed on 2026-07-01.

### Phase R7: Course Teaching Redesign - Part 7

Plan: `redesign/docs/plans/2026-07-02-phase-r7-course-teaching-redesign.md`

Status: Planned.

Purpose:

- Rewrite Part 7 so Production Readiness starts from the local paper research assistant's "can we replay, audit, and block unsafe runs before real deployment?" problem.
- Teach `RunDiagnostics`, `JsonlRunEventStore`, `ApprovalPolicy`, `SandboxPolicy`, and docs freshness as local-first production boundaries.
- Add the three Part 7 files to the markdown Python block gate after the rewrite normalizes every error-demonstrating block.

Exit criteria:

- Chapter/Lab/Solution 07 are rewritten using the R1-R6 teaching contract.
- `course/README.md`, `README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` describe Part 7 as R7 rewritten after content lands.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run ruff check .` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q` passes.
- `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q` passes for Parts 0-7.
- `cd redesign/apps/web && npm ci && npm run build` passes.

# Study Agent Redesign

This is the clean-room redesign version of the Study Agent project.

## Purpose

The redesign is both a course and a product reference:

- Course layer: learn modern Agent engineering from first principles.
- Product layer: build a professional Research Agent Workbench.
- Shared core: keep runtime contracts testable, offline-first, and framework-independent.

## Current Scope

Phase 0 created the scaffold:

- Python package boundary under `packages/research_core`.
- Minimal runtime message and event contracts.
- Fake model fixture baseline.
- Offline pytest and ruff baseline.
- Architecture docs and glossary.

Phase 1 adds the first Agent Kernel course spine:

- `ToolRuntime`, `ContextBuilder`, `AgentRunner`, and trajectory helpers.
- Deterministic model/tool/event tests.
- Beginner-ready course entrypoint, reference primers, Chapter 00, Lab 00, Chapter 01, Lab 01, and solutions under `course/`.

Phase 2 adds the first Research Core contracts:

- `Project`, `ResearchRun`, `Source`, `Evidence`, `Claim`, and `Report`.
- Deterministic `SourceIngestor` and offline `FakeRetriever`.
- Claim-source mapping helpers for citation-quality tests.

Phase 3 adds the first stateful-agent contracts:

- `MemoryEngine`, `MemoryRecord`, recall policy, and write policy.
- `SkillRuntime` and `SkillPackage` for folder-based progressive disclosure.
- Memory pollution and skill loading eval cases.

Phase 4 adds the first multi-agent delegation contracts:

- `AgentRolePolicy`, `DelegationTask`, `DelegationBudget`, and merge results.
- `DelegationRuntime` for deterministic child-agent orchestration and parent delegation events.
- `A2AAdapterStub` for a local, non-network remote-agent boundary.
- Child context isolation, budget accounting, A2A export, and merge eval cases.

Phase 5 adds the first Workbench Product surface:

- `research_core.product.WorkbenchSnapshot` and panel contracts for project, run, timeline, delegation, sources, report, memory, skills, and evals.
- FastAPI read API under `apps/api` with `/health`, `/api/workbench/snapshot`, and `/api/workbench/timeline`.
- React + TypeScript + Vite Workbench under `apps/web`, with API loading and deterministic fallback fixture.
- Product integration course material in Chapter/Lab/Solution 05.

Phase 6 adds controlled Framework Comparisons:

- `course/framework_comparisons` contains shared comparison tasks, handwritten runner baselines, deterministic framework profiles, and recommendation reports.
- Course Chapter/Lab/Solution 06 teaches how to compare frameworks using the same task, fake fixtures, trajectory checks, and task weights.
- Framework code remains course material and does not enter `research_core`, `apps/api`, or `apps/web`.

Phase 7 adds the first Production Readiness contracts:

- `research_core.production.RunDiagnostics` summarizes `RunEvent` trajectories for offline observability.
- `JsonlRunEventStore` stores append-only run events without introducing a database dependency.
- `ApprovalPolicy` and `SandboxPolicy` model production permission decisions before real auth or sandbox infrastructure exists.
- `infra/docs_freshness.py` keeps course/docs indexes honest.
- Course Chapter/Lab/Solution 07 teaches production readiness as local contracts.

Phase R1 adds the first project-driven course teaching rewrite:

- The learner entrypoint now frames the course as building a 本地论文研究助手.
- Part 1 Chapter/Lab/Solution materials now teach the Agent Kernel through mental models, event-trail inspection, break/fix loops, three-tier exercises, and design rationale.
- `docs/course/roadmap.md` and `docs/course/chapter-template.md` define the Part-based teaching contract for R2-R9.
- `course/capstone/README.md` previews the full offline Capstone without claiming it is implemented yet.

Phase R2 adds the second project-driven course teaching rewrite:

- Part 2 Chapter/Lab/Solution materials now teach Research Core through the citation problem: source -> evidence -> claim -> report -> claim-source link.
- Lab 02 now uses L1 Follow, L2 Modify, broken-link diagnosis, and L3 Design exercises with feedback loops.
- Solution 02 explains what each assertion proves and why the evidence-chain design matters for Memory, Delegation, Workbench, and Production Diagnostics.

Real retrieval adapters, async delegation, streaming, real auth, real cloud deployment, real A2A transport, and live framework adapters arrive in later phases.

## Course Entry

Start at `course/README.md`. New learners should follow the Beginner Track before Chapter 01; experienced engineers can skim the glossary and jump to the Agent Kernel lab.

Current course coverage follows the implemented runtime phases. Phase R1 rewrote the learner entrypoint and Part 1 into the project-driven teaching style; Phase R2 rewrote Part 2. Parts 3-7 remain current v1 course material until their planned R3-R7 rewrites.

- Chapter/Lab/Solution 00: learner setup and pre-kernel mental model.
- Chapter/Lab/Solution 01: Agent Kernel.
- Chapter/Lab/Solution 02: Research Core, R2 project-driven rewrite.
- Chapter/Lab/Solution 03: Memory and Skills.
- Chapter/Lab/Solution 04: Multi-Agent Delegation.
- Chapter/Lab/Solution 05: Workbench Product.
- Chapter/Lab/Solution 06: Framework Comparisons.
- Chapter/Lab/Solution 07: Production Readiness.

## Commands

Run from this directory:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm install && npm run build
```

## Boundaries

Legacy code remains outside this folder. New redesign work should live under `redesign/` unless an approved phase plan explicitly says otherwise.

## Verification

Expected local checks:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm run build
```

The pytest suite should include runtime, fake provider, research core, memory,
skill, delegation, product snapshot, API, production-readiness, and docs
freshness tests. The web build should pass when `apps/web` dependencies are
installed.

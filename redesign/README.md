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
- Capstone began as a placeholder in R1; the full project materials land in Phase R8.

Phase R2 adds the second project-driven course teaching rewrite:

- Part 2 Chapter/Lab/Solution materials now teach Research Core through the citation problem: source -> evidence -> claim -> report -> claim-source link.
- Lab 02 now uses L1 Follow, L2 Modify, broken-link diagnosis, and L3 Design exercises with feedback loops.
- Solution 02 explains what each assertion proves and why the evidence-chain design matters for Memory, Delegation, Workbench, and Production Diagnostics.

Phase R3 adds the third project-driven course teaching rewrite:

- Part 3 Chapter/Lab/Solution materials now teach Memory and Skills through the repeated-session notebook problem: memory write/recall policy, six `MemoryKind` labels, deterministic recall ordering, skill package manifests, and explicit reference reads.
- Lab 03 now uses L1 Follow, L2 Modify, Memory/Skill Break/Fix checks, and an open-ended L3 Design exercise graded by invariants.
- `infra/markdown_python_blocks.py` and `tests/course/test_markdown_python_blocks.py` execute fenced Python course examples against the local `research_core` API.

Phase R4 adds the fourth project-driven course teaching rewrite:

- Part 4 Chapter/Lab/Solution materials now teach Multi-Agent Delegation through the delegated-review problem: child context isolation, step-budget accounting, parent delegation event trails, and unresolved-conflict visibility.
- Lab 04 now uses L1 Follow, L2 Modify/Break-Fix checks, and an open-ended L3 Design exercise graded by delegation invariants.
- The markdown Python block gate now covers setup material plus Parts 1-4 chapter/lab/solution files.

Phase R5 adds the fifth project-driven course teaching rewrite:

- Part 5 Chapter/Lab/Solution materials now teach Workbench Product through the "give the researcher an inspectable workbench without inventing a separate data model" problem: the `from_*` adapters that turn raw domain objects into panel items, `summary_row()` projections, `WorkbenchSnapshot` referential-integrity validation, and the downward-only core -> FastAPI -> React boundary.
- Lab 05 now uses L1 Follow, L2 Modify/Break-Fix checks, and an open-ended L3 Design exercise graded by snapshot invariants.
- The markdown Python block gate now also runs `apps/api/src` blocks and covers setup material plus Parts 1-5 chapter/lab/solution files.

Phase R6 adds the sixth project-driven course teaching rewrite:

- Part 6 Chapter/Lab/Solution materials now teach Framework Comparisons through the "why not just use LangChain/CrewAI?" build-vs-adopt decision: a pinned task/fixture/metric and a transparent weighted score (`ComparisonTask` weights x `FrameworkProfile` scores -> `FrameworkRecommendation`), with the `>=0.8` strengths / `<0.55` tradeoffs derivation and the deterministic tie-break.
- Lab 06 now uses L1 Follow, L2 Modify/Break-Fix checks, and an open-ended L3 Design exercise graded by a predicted-winner invariant.
- The markdown Python block gate now covers setup material plus Parts 1-6 chapter/lab/solution files; no gate helper change was needed because `course.framework_comparisons` already imports under the gate.

Phase R7 adds the seventh project-driven course teaching rewrite:

- Part 7 Chapter/Lab/Solution materials now teach Production Readiness through the "can we replay, audit, and block unsafe runs before real deployment?" problem: `RunDiagnostics`, `JsonlRunEventStore`, `ApprovalPolicy`, `SandboxPolicy`, and docs freshness as local-first contracts.
- Lab 07 now uses L1 Follow, L2 Modify/Break-Fix checks, and an open-ended L3 Design exercise for a report-export readiness boundary.
- The markdown Python block gate now covers setup material plus Parts 1-7 chapter/lab/solution files.

Phase R8 adds the full Capstone project:

- `course/capstone/README.md` is the real product brief (no longer a placeholder).
- Paper fixtures, rubric, starter skeleton, reference solution, trajectory, sample report, and reflection ship under `course/capstone/`.
- Capstone stays offline with FakeModel, FakeRetriever, and static paper fixtures; solution tests prove the six rubric success criteria.
- Capstone tests live under `course/capstone/` and are run explicitly (outside default `tests/` paths).

Phase R9 adds reference and support materials:

- `course/reference/common-patterns.md`, `course/reference/troubleshooting.md`, `course/reference/design-decisions-index.md`, and `course/reference/discussion-prompts.md` (with detailed answers).
- `course/reference/agent-kernel-glossary.md` expanded for Parts 1–7 + Capstone.
- Course/docs indexes link the full reference set; R1–R9 teaching redesign is complete.

Phase F0–F1 scaffold and start parallel framework teaching tracks (does not replace handwritten R1–R9):

- `course/tracks/langchain/` and `course/tracks/langgraph/` entrypoints.
- Teaching packages `packages/langchain_course` and `packages/langgraph_course` (optional uv groups; not product runtime).
- DeepSeek via env or local `.env` (gitignored); hello lab + LC Parts 1–2 (agent kernel + evidence chain).
- LC track F0–F3 complete (Parts 1–7 + Capstone). Full LG track (F4–F5) is planned.

Real retrieval adapters, async delegation, streaming, real auth, real cloud deployment, real A2A transport, and live framework product adapters arrive in later phases.

## Course Entry

Start at `course/README.md`. New learners should follow the Beginner Track before Chapter 01; experienced engineers can skim the glossary and jump to the Agent Kernel lab.

Current course coverage follows the implemented runtime phases. Phase R1 rewrote the learner entrypoint and Part 1 into the project-driven teaching style; Phase R2 rewrote Part 2; Phase R3 rewrote Part 3; Phase R4 rewrote Part 4; Phase R5 rewrote Part 5; Phase R6 rewrote Part 6; Phase R7 rewrote Part 7; Phase R8 completed the Capstone under `course/capstone/`; Phase R9 completed reference and support materials under `course/reference/`.

- Chapter/Lab/Solution 00: learner setup and pre-kernel mental model.
- Chapter/Lab/Solution 01: Agent Kernel.
- Chapter/Lab/Solution 02: Research Core, R2 project-driven rewrite.
- Chapter/Lab/Solution 03: Memory and Skills, R3 project-driven rewrite.
- Chapter/Lab/Solution 04: Multi-Agent Delegation, R4 project-driven rewrite.
- Chapter/Lab/Solution 05: Workbench Product, R5 project-driven rewrite.
- Chapter/Lab/Solution 06: Framework Comparisons, R6 project-driven rewrite.
- Chapter/Lab/Solution 07: Production Readiness, R7 project-driven rewrite.
- Capstone (R8): full offline 本地论文研究助手 under `course/capstone/`.
- Reference (R9): patterns, troubleshooting, design-decision index, discussion prompts with answers, glossary.
- Parallel framework tracks (F0+): `course/tracks/langchain/`, `course/tracks/langgraph/` (LC then LG; DeepSeek by default).

## Commands

Run from this directory:

```bash
uv run pytest -q
uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py course/capstone/starter/test_starter.py -q
cd apps/web && npm install && npm run build
```

## Boundaries

Legacy code remains outside this folder. New redesign work should live under `redesign/` unless an approved phase plan explicitly says otherwise.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for the Python toolchain (`curl -LsSf https://astral.sh/uv/install.sh | sh` on macOS/Linux)
- Node.js + npm for `apps/web` builds

## Verification

Expected local checks:

```bash
uv run pytest -q
uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py course/capstone/starter/test_starter.py -q
cd apps/web && npm run build
```

The pytest suite under `tests/` includes runtime, fake provider, research core, memory,
skill, delegation, product snapshot, API, production-readiness, and docs
freshness tests. Capstone tests live under `course/capstone/` and are run with the
explicit command above. The web build should pass when `apps/web` dependencies are
installed.

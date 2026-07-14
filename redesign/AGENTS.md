# Agent Instructions for Study Agent Redesign

## Scope

These instructions apply to files under `redesign/`.

## Rules

- Keep `packages/research_core` independent from FastAPI, React, databases, and provider SDKs.
- Keep tests offline by default.
- Use `FakeModel` and public `research_core.runtime` contracts for offline runtime tests and labs.
- Keep `research_core.research` independent from product apps, databases, provider SDKs, embeddings, and legacy root code.
- Keep `research_core.memory` and `research_core.skills` offline-first and independent from product apps, databases, provider SDKs, embeddings, and legacy root code.
- Keep `research_core.delegation` deterministic, offline-first, and independent from product apps, provider SDKs, network transport, and legacy root code.
- Keep `research_core.product` independent from FastAPI, React, databases, provider SDKs, and network transport. Product contracts should expose JSON-compatible `to_record()` data for API/UI layers.
- Keep `research_core.production` offline-first and independent from FastAPI, React, provider SDKs, databases, cloud services, and real auth. Production-readiness contracts should be inspectable policy/diagnostic/storage boundaries before real infrastructure adapters exist.
- Keep framework comparison code under `course/framework_comparisons/`; do not import third-party agent frameworks into `research_core`, `apps/api`, or `apps/web` without an approved later-phase plan.
- Keep Capstone teaching artifacts under `course/capstone/`; Capstone may compose public `research_core` contracts but must not grow a product package or require network/provider access.
- Keep `packages/langchain_course` and `packages/langgraph_course` teaching-only; do not import them from `research_core`, `apps/api`, or `apps/web`.
- Keep framework track materials under `course/tracks/langchain/` and `course/tracks/langgraph/`; do not mix their code with handwritten Capstone under `course/capstone/`.
- Framework track live API tests require `DEEPSEEK_API_KEY` (env or gitignored `.env`) and `RUN_DEEPSEEK_TESTS=1`; default CI stays offline. Never commit real keys.
- Keep `apps/api` as a transport layer over `research_core.product`; do not put domain logic, provider calls, or persistence shortcuts there without an approved later-phase plan.
- Keep `apps/web` consuming the Workbench API record shape or a matching deterministic fallback fixture; do not let React components invent a separate product data model.
- Use `SourceIngestor` and `FakeRetriever` for deterministic offline research tests.
- Use `MemoryEngine` and `SkillRuntime` for deterministic memory/skill tests.
- Use `DelegationRuntime` and `A2AAdapterStub` for deterministic delegation tests; do not add real A2A transport without an approved later-phase plan.
- Add or update docs when a runtime concept is introduced.
- Keep learner-facing course docs beginner-ready: include prerequisites, plain-language mental model, runnable offline examples, failure inspection, eval gate, and solution notes.
- When a phase introduces a new learner-facing runtime concept, update `course/README.md`, `docs/course/roadmap.md`, and the relevant chapter/lab/solution files in the same phase or record an explicit deferral.
- Do not import from the legacy root `app/` or `frontend/` directories.
- Store redesign specs and plans under `redesign/docs/`.
- Keep runner failures observable: model, tool, malformed-call, unknown-tool, and budget errors should append `RunEventType.ERROR` before raising.

## Verification

Before claiming completion for a redesign change, run:

```bash
uv run pytest -q
uv run ruff check .
```

For changes that touch `apps/web`, also run:

```bash
cd apps/web && npm run build
```

For course markdown changes that include runnable Python examples, also run:

```bash
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
```

This gate covers the handwritten setup/Parts 1–7 files and all 23 LangChain
track chapter/lab/solution files. Blocks that intentionally require a live key
must use a `python-live` fence so the offline gate does not call external APIs.

For Capstone changes, also run:

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py course/capstone/starter/test_starter.py -q
```

This gate currently covers setup material plus Parts 1-7 chapter/lab/solution
files in the handwritten course plus the LangChain parallel track, and it
compares stdout for blocks followed by an `Expected output:` text fence.
Capstones are covered by dedicated tests rather than the Markdown block gate.

`uv.lock` is intentionally tracked from F3R onward so framework-course installs
reuse the verified LangChain 1.x dependency set.

## Architecture Direction

The runtime should follow these boundaries:

- Internal messages are `AgentMessage`, not provider messages.
- Runtime activity is recorded as `RunEvent`.
- Phase 1 runtime flow is `ContextBuilder -> AgentRunner -> ToolRuntime -> RunEvent`.
- Phase 2 research flow is `SourceInput -> SourceIngestor -> FakeRetriever -> Evidence -> Claim -> Report -> ClaimSourceLink`.
- Phase 3 stateful flow is `MemoryWritePolicy -> MemoryEngine -> MemoryRecallPolicy` and `SkillRuntime -> SKILL.md -> explicit references`.
- Phase 4 delegation flow is `DelegationTask -> DelegationRuntime -> delegate_* RunEvent records -> DelegationResult -> DelegationMergeResult`, with `A2AAdapterStub` limited to deterministic export stubs.
- Phase 5 product flow is `runtime/research/memory/skills/delegation objects -> WorkbenchSnapshot.to_record() -> research_api FastAPI endpoints -> apps/web React panels`.
- Phase 6 comparison flow is `ComparisonTask -> handwritten AgentRunner baseline -> FrameworkProfile -> FrameworkRecommendation matrix`, all under `course/framework_comparisons/`.
- Phase 7 production-readiness flow is `RunEvent -> RunDiagnostics`, `RunEvent -> JsonlRunEventStore`, and tool/path/network subjects -> approval/sandbox decisions, all offline and testable.
- Capstone flow (R8) composes Parts 1-7 offline under `course/capstone/`: fixtures -> evidence chain -> memory/skill -> optional delegation -> WorkbenchSnapshot -> production trust evidence.
- Provider adapters convert at the boundary.
- Fake model providers are first-class testing infrastructure.

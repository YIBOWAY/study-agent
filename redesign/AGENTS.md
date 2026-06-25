# Agent Instructions for Study Agent Redesign

## Scope

These instructions apply to files under `redesign/`.

## Rules

- Keep `packages/research_core` independent from FastAPI, React, databases, and provider SDKs.
- Keep tests offline by default.
- Use `FakeModel` and public `research_core.runtime` contracts for offline runtime tests and labs.
- Keep `research_core.research` independent from product apps, databases, provider SDKs, embeddings, and legacy root code.
- Keep `research_core.memory` and `research_core.skills` offline-first and independent from product apps, databases, provider SDKs, embeddings, and legacy root code.
- Use `SourceIngestor` and `FakeRetriever` for deterministic offline research tests.
- Use `MemoryEngine` and `SkillRuntime` for deterministic memory/skill tests.
- Add or update docs when a runtime concept is introduced.
- Do not import from the legacy root `app/` or `frontend/` directories.
- Store redesign specs and plans under `redesign/docs/`.
- Keep runner failures observable: model, tool, malformed-call, unknown-tool, and budget errors should append `RunEventType.ERROR` before raising.

## Verification

Before claiming completion for a redesign change, run:

```bash
uv run pytest -q
uv run ruff check .
```

## Architecture Direction

The runtime should follow these boundaries:

- Internal messages are `AgentMessage`, not provider messages.
- Runtime activity is recorded as `RunEvent`.
- Phase 1 runtime flow is `ContextBuilder -> AgentRunner -> ToolRuntime -> RunEvent`.
- Phase 2 research flow is `SourceInput -> SourceIngestor -> FakeRetriever -> Evidence -> Claim -> Report -> ClaimSourceLink`.
- Phase 3 stateful flow is `MemoryWritePolicy -> MemoryEngine -> MemoryRecallPolicy` and `SkillRuntime -> SKILL.md -> explicit references`.
- Provider adapters convert at the boundary.
- Fake model providers are first-class testing infrastructure.

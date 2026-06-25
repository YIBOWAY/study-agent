# Agent Instructions for Study Agent Redesign

## Scope

These instructions apply to files under `redesign/`.

## Rules

- Keep `packages/research_core` independent from FastAPI, React, databases, and provider SDKs.
- Keep tests offline by default.
- Use fake model fixtures for Phase 0 baseline tests.
- Add fake search/retrieval fixtures only when the Research Core phase introduces retrieval contracts.
- Add or update docs when a runtime concept is introduced.
- Do not import from the legacy root `app/` or `frontend/` directories.
- Store redesign specs and plans under `redesign/docs/`.

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
- Provider adapters convert at the boundary.
- Fake model providers are first-class testing infrastructure.

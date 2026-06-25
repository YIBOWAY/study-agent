# Phase 0 Progress: Redesign Scaffold

Status: Complete

Started: 2026-06-25
Completed: 2026-06-25
Branch: `codex/redesign-phase-0`
Commit: `f33fe35 feat: scaffold redesign phase 0`

## Delivered

- Created the self-contained `redesign/` workspace shell.
- Added `redesign/README.md`, `redesign/AGENTS.md`, and `redesign/pyproject.toml`.
- Added app, course, eval, and infra placeholders.
- Added architecture docs and glossary.
- Added `research_core` runtime contracts:
  - `AgentMessage`
  - `RunEvent`
  - recursive immutability helpers
  - strict JSON-compatible event payloads
- Added `FakeModel` and `FakeModelResponse` for offline tests.
- Added 33 tests across message, event, and fake model behavior.

## Verification

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

Recorded result on 2026-06-25:

- `33 passed`
- `All checks passed!`

## Notes For Agents

- Fake search/retrieval is intentionally deferred to Phase 2.
- Do not import from legacy `app/` or `frontend/`.
- Continue new work under `redesign/` unless an approved phase plan says otherwise.

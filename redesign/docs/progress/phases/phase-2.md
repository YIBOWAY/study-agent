# Phase 2 Progress: Research Core

Status: In Progress

Started: 2026-06-25
Completed: Not completed
Branch: `codex/redesign-phase-1`

## Goal

Add research domain entities, fake retrieval, source ingestion, and claim-source mapping tests.

## Start Conditions

- Phase 1 runtime contracts are stable.
- Agent runner events and trajectory tests are available for research workflows.

## Planned Deliverables

- Phase 2 executable plan under `redesign/docs/plans/`.
- Research entities: `Project`, `ResearchRun`, `Source`, `Evidence`, `Claim`, and `Report`.
- Deterministic local source ingestion.
- Deterministic fake retrieval for offline tests and future evals.
- Claim-source mapping helpers and tests.
- Data model architecture docs and glossary updates.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-25 | Phase 2 started from Phase 1 baseline. Verification before changes: `uv run pytest -q` -> `78 passed`; `uv run ruff check .` -> `All checks passed!`. |

## Verification Target

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

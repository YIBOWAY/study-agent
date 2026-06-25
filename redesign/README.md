# Study Agent Redesign

This is the clean-room redesign version of the Study Agent project.

## Purpose

The redesign is both a course and a product reference:

- Course layer: learn modern Agent engineering from first principles.
- Product layer: build a professional Research Agent Workbench.
- Shared core: keep runtime contracts testable, offline-first, and framework-independent.

## Phase 0 Scope

Phase 0 creates the scaffold:

- Python package boundary under `packages/research_core`.
- Minimal runtime message and event contracts.
- Fake model fixture baseline.
- Offline pytest and ruff baseline.
- Architecture docs and glossary.

Fake search and retrieval fixtures arrive with the Research Core phase.

## Commands

Run from this directory:

```bash
uv run pytest -q
uv run ruff check .
```

## Boundaries

Legacy code remains outside this folder. New redesign work should live under `redesign/` unless an approved phase plan explicitly says otherwise.

## Phase 0 Verification

Expected local checks:

```bash
uv run pytest -q
uv run ruff check .
```

The pytest suite should include runtime message, event, and fake provider tests.

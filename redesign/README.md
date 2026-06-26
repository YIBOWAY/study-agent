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

Product APIs, delegation, persistence, and real retrieval adapters arrive in later phases.

## Course Entry

Start at `course/README.md`. New learners should follow the Beginner Track before Chapter 01; experienced engineers can skim the glossary and jump to the Agent Kernel lab.

## Commands

Run from this directory:

```bash
uv run pytest -q
uv run ruff check .
```

## Boundaries

Legacy code remains outside this folder. New redesign work should live under `redesign/` unless an approved phase plan explicitly says otherwise.

## Verification

Expected local checks:

```bash
uv run pytest -q
uv run ruff check .
```

The pytest suite should include runtime, fake provider, research core, memory, and skill tests.

# Phase 3 Progress: Memory and Skills

Status: In Progress

Started: 2026-06-26
Completed: Not completed
Branch: `codex/redesign-phase-3`

## Goal

Add memory recall/write policies, skill runtime, and memory/skill eval cases.

## Start Conditions

- Phase 2 research entities are available.
- Research runs have stable source, evidence, and report contracts.

## Planned Deliverables

- Phase 3 executable plan under `redesign/docs/plans/`.
- `MemoryRecord`, `MemoryKind`, `MemoryWritePolicy`, `MemoryRecallPolicy`, and `MemoryEngine`.
- `SkillPackage` and `SkillRuntime` with folder-based progressive disclosure.
- Memory pollution and skill loading eval cases.
- Runtime event enum alignment for Phase 3-adjacent comprehensive event values.
- Architecture docs, glossary, root README, and AGENTS updates.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-26 | Phase 3 started from Phase 2 baseline. Verification before changes: `uv run pytest -q` -> `100 passed`; `uv run ruff check .` -> `All checks passed!`. |

## Verification Target

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

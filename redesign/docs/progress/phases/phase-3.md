# Phase 3 Progress: Memory and Skills

Status: Complete

Started: 2026-06-26
Completed: 2026-06-26
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
| 2026-06-26 | Memory engine delivered: `MemoryKind`, `MemoryRecord`, `MemoryWritePolicy`, `MemoryRecallPolicy`, and `MemoryEngine` with immutable records, JSON-compatible metadata, write policy rejection, deterministic token recall, and pinned-first ordering. Verification: `uv run pytest tests/research_core/test_memory_engine.py -q` -> `8 passed`; scoped `ruff` clean. |
| 2026-06-26 | Skill runtime delivered: `SkillPackage` and `SkillRuntime` load `SKILL.md`, extract frontmatter metadata, discover references/scripts/assets without reading reference content, and enforce reference path boundaries. Verification: `uv run pytest tests/research_core/test_skill_runtime.py -q` -> `6 passed`; scoped `ruff` clean. |
| 2026-06-26 | Memory/skill eval cases and event enum alignment delivered: memory pollution rejection, explicit skill reference loading, and `RunEventType` values for `skill_step`, `delegate_event`, `compaction_start`, `compaction_finish`, and `eval_result`. Verification: `uv run pytest tests/research_core/test_events.py tests/research_core/test_memory_skill_evals.py -q` -> `17 passed`; scoped `ruff` clean. |
| 2026-06-26 | Phase 3 docs synchronized: runtime architecture, data model, glossary, docs index, root README, AGENTS instructions, roadmap, and progress docs now reflect Memory and Skills. Final verification: `uv run pytest -q` -> `116 passed`; `uv run ruff check .` -> `All checks passed!`; `git diff --check` clean. |

## Delivered Files

- `packages/research_core/src/research_core/memory/__init__.py`
- `packages/research_core/src/research_core/memory/engine.py`
- `packages/research_core/src/research_core/skills/__init__.py`
- `packages/research_core/src/research_core/skills/runtime.py`
- `tests/research_core/test_memory_engine.py`
- `tests/research_core/test_skill_runtime.py`
- `tests/research_core/test_memory_skill_evals.py`

## Next Focus

Phase 4 planning: delegation runtime, isolated child contexts, role policies, budget accounting, and merge contracts.

## Verification

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

Recorded final result on 2026-06-26:

- `116 passed`
- `All checks passed!`
- `git diff --check` clean

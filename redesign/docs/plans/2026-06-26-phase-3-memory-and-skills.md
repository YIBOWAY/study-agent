# Memory and Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first stateful-agent layer: memory records with recall/write policies, a folder-based skill runtime, memory/skill eval cases, event enum alignment, and synchronized docs.

**Architecture:** Phase 3 introduces `research_core.memory` and `research_core.skills` packages that remain independent from apps, databases, provider SDKs, embeddings, and legacy root code. The memory layer is deterministic and in-process; the skill layer uses progressive disclosure by loading `SKILL.md` first and exposing references/scripts/assets only as paths until explicitly read.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, enums, pathlib, strict JSON-compatible metadata.

---

## File Structure

Create or update these files:

- Create: `redesign/packages/research_core/src/research_core/memory/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/memory/engine.py`
- Create: `redesign/packages/research_core/src/research_core/skills/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/skills/runtime.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/events.py`
- Modify: `redesign/tests/research_core/test_events.py`
- Create: `redesign/tests/research_core/test_memory_engine.py`
- Create: `redesign/tests/research_core/test_skill_runtime.py`
- Create: `redesign/tests/research_core/test_memory_skill_evals.py`
- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/architecture/data-model.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-3.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy `app/`, `frontend/`, root `tests/`, root `eval/`, provider SDK code, or product app placeholders.

## Contracts

### Memory

- `MemoryKind`: `working`, `session`, `episodic`, `semantic`, `procedural`, and `pinned`.
- `MemoryRecord`: immutable record with `id`, `kind`, `content`, `tags`, `importance`, and JSON-compatible metadata.
- `MemoryWritePolicy`: validates writes with allowed kinds, minimum importance, maximum content length, and forbidden phrases.
- `MemoryRecallPolicy`: deterministic recall with query, allowed kinds, limit, and pinned-first ordering.
- `MemoryEngine`: in-process store with `write(record)` and `recall(policy)`.

Memory recall is token based and deterministic. It is not embeddings, long-term persistence, or conflict resolution yet.

### Skills

- `SkillPackage`: immutable loaded skill with `name`, `root`, `entrypoint`, and discovered `references`, `scripts`, and `assets` paths.
- `SkillRuntime.load(path)`: validates a skill directory, reads only `SKILL.md`, extracts frontmatter `name` and `description`, and discovers child resources.
- `SkillRuntime.read_reference(package, relative_path)`: explicit progressive-disclosure read of a reference file under `references/`.

Skill runtime rejects missing `SKILL.md`, blank names, path traversal, and reference reads outside the skill root.

### Eval Cases

- Memory pollution eval proves generic or forbidden writes are rejected by `MemoryWritePolicy`.
- Skill loading eval proves entrypoint loading does not read reference content until explicitly requested.
- Runtime event enum is aligned with the comprehensive event stream for Phase 3-adjacent events: `skill_step`, `delegate_event`, `compaction_start`, `compaction_finish`, and `eval_result`.

## Task 1: Add Phase 3 Plan and Start Progress

**Files:**

- Create: `redesign/docs/plans/2026-06-26-phase-3-memory-and-skills.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-3.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this Phase 3 plan**

Save this plan at `redesign/docs/plans/2026-06-26-phase-3-memory-and-skills.md`.

- [x] **Step 2: Mark Phase 3 as active**

Update the progress dashboard so Phase 3 is in progress and the verification baseline records the Phase 2 final baseline before Phase 3 changes.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "phase-3-memory-and-skills|Phase 3|MemoryEngine|SkillRuntime" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: the Phase 3 plan and active progress state are discoverable from the docs index, roadmap, and progress dashboard.

## Task 2: Add Memory Engine

**Files:**

- Create: `redesign/packages/research_core/src/research_core/memory/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/memory/engine.py`
- Create: `redesign/tests/research_core/test_memory_engine.py`
- Modify: `redesign/docs/progress/phases/phase-3.md`

- [x] **Step 1: Write failing tests**

Create tests for:

- `MemoryRecord` rejects blank IDs/content and invalid importance values;
- metadata and tags are copied and immutable;
- `MemoryWritePolicy` rejects disallowed kinds, low importance, overlong content, and forbidden phrases;
- `MemoryEngine.write()` stores accepted records and returns the stored record;
- `MemoryEngine.recall()` returns deterministic pinned-first token matches with a positive limit.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_memory_engine.py -q
```

Expected: failure because `research_core.memory` does not exist.

- [x] **Step 3: Implement memory contracts**

Create `MemoryKind`, `MemoryRecord`, `MemoryWritePolicy`, `MemoryRecallPolicy`, and `MemoryEngine`. Reuse `freeze_json_value` for metadata and keep recall deterministic.

- [x] **Step 4: Export memory contracts**

Update `research_core.memory.__init__` to export all public Phase 3 memory contracts.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_memory_engine.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/memory tests/research_core/test_memory_engine.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 3: Add Skill Runtime

**Files:**

- Create: `redesign/packages/research_core/src/research_core/skills/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/skills/runtime.py`
- Create: `redesign/tests/research_core/test_skill_runtime.py`
- Modify: `redesign/docs/progress/phases/phase-3.md`

- [x] **Step 1: Write failing tests**

Create tests for:

- `SkillRuntime.load()` reads `SKILL.md` and extracts `name` and `description`;
- loading discovers `references`, `scripts`, and `assets` paths without reading reference content;
- missing `SKILL.md` and blank skill names are rejected;
- `read_reference()` reads only files under `references/`;
- path traversal and files outside the skill root are rejected.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_skill_runtime.py -q
```

Expected: failure because `research_core.skills` does not exist.

- [x] **Step 3: Implement skill runtime**

Create `SkillPackage` and `SkillRuntime` with pathlib-based path validation and simple YAML-frontmatter extraction for `name` and `description`.

- [x] **Step 4: Export skill contracts**

Update `research_core.skills.__init__`.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_skill_runtime.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/skills tests/research_core/test_skill_runtime.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 4: Add Eval Cases and Event Alignment

**Files:**

- Modify: `redesign/packages/research_core/src/research_core/runtime/events.py`
- Modify: `redesign/tests/research_core/test_events.py`
- Create: `redesign/tests/research_core/test_memory_skill_evals.py`
- Modify: `redesign/docs/progress/phases/phase-3.md`

- [x] **Step 1: Write failing tests**

Update event tests to expect `skill_step`, `delegate_event`, `compaction_start`, `compaction_finish`, and `eval_result`.

Create eval tests for:

- memory pollution rejection through `MemoryWritePolicy`;
- explicit skill reference loading through `SkillRuntime`.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_events.py tests/research_core/test_memory_skill_evals.py -q
```

Expected: failure because new event enum values and eval module behavior are not complete yet.

- [x] **Step 3: Implement event enum alignment**

Add the missing event enum values while preserving existing values and JSON record behavior.

- [x] **Step 4: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_events.py tests/research_core/test_memory_skill_evals.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/events.py tests/research_core/test_events.py tests/research_core/test_memory_skill_evals.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 5: Update Architecture, Glossary, README, and Progress

**Files:**

- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/architecture/data-model.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-3.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Update runtime architecture**

Document memory write/recall policy, skill progressive disclosure, and Phase 3 event enum alignment.

- [x] **Step 2: Update data model and glossary**

Add `MemoryRecord`, `MemoryWritePolicy`, `MemoryRecallPolicy`, `MemoryEngine`, `SkillPackage`, and `SkillRuntime`.

- [x] **Step 3: Update root docs and progress**

Mark Phase 3 complete only after final verification passes.

- [x] **Step 4: Verify docs**

Run:

```bash
rg -n "MemoryEngine|MemoryRecord|MemoryWritePolicy|MemoryRecallPolicy|SkillRuntime|SkillPackage|progressive disclosure|memory pollution" redesign/docs redesign/README.md redesign/AGENTS.md
```

Expected: Phase 3 concepts are discoverable from docs, architecture, glossary, and progress.

## Task 6: Final Phase 3 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-3.md`

- [x] **Step 1: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
git diff --check
```

Expected:

```text
All tests pass.
All checks passed!
No whitespace errors.
```

- [x] **Step 2: Clean generated side effects**

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, and any `__pycache__` directories unless an approved plan adds them as tracked artifacts.

- [x] **Step 3: Commit and push**

Commit with a message that records the Phase 3 deliverables and verification commands. Push branch `codex/redesign-phase-3`.

## Phase 3 Completion Checklist

- [x] Memory engine contracts are implemented and exported.
- [x] Memory engine tests pass.
- [x] Skill runtime contracts are implemented and exported.
- [x] Skill runtime tests pass.
- [x] Memory pollution and skill loading eval cases pass.
- [x] Runtime event enum includes Phase 3-adjacent comprehensive event values.
- [x] Architecture, glossary, README, AGENTS, roadmap, and progress docs are updated.
- [x] `cd redesign && uv run pytest -q` passes.
- [x] `cd redesign && uv run ruff check .` passes.
- [x] `git diff --check` is clean.
- [x] No legacy `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.

# Phase F2: LangChain Parts 3–4 — Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver LangChain track Parts 3–4 (Memory/Skills + multi-agent delegation) as framework-native teaching code and course materials, without `research_core` mix or offline main CI breakage.

**Architecture:** Teaching-only `langchain_course` modules implement an in-memory notebook with write/recall policy, progressive skill package loading, and a sequential multi-worker delegation runtime with budgets, isolated child context, parent step trail, and merge conflicts. Course materials under `course/tracks/langchain/` mirror the main Part contract.

**Tech Stack:** Same as F1 (`langchain-core`, `langchain-openai`, `python-dotenv`, pytest, ruff). No LangGraph.

**Spec:** `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`

## Global Constraints

- Zero import between `langchain_course` and `research_core`.
- Secrets only via env / gitignored `.env`.
- Main `pytest -q` stays offline green without LC group or key.
- LC track still must not require `langgraph`.
- Chinese user-facing track docs; agent commits/pushes.

---

### Task 1: Part 3 code — memory + skills

**Files:**
- Create: `packages/langchain_course/src/langchain_course/memory.py`
- Create: `packages/langchain_course/src/langchain_course/skills.py`
- Create: `packages/langchain_course/tests/test_memory.py`
- Create: `packages/langchain_course/tests/test_skills.py`

**Interfaces:**
- `MemoryKind` str enum: note, preference, fact, warning, pinned, scratch
- `MemoryNote(id, kind, content, tags, importance, pinned: bool)`
- `MemoryWritePolicy(allowed_kinds, min_importance, banned_substrings, max_content_len)`
- `MemoryRecallPolicy(query, allowed_kinds, limit, pinned_first)`
- `Notebook.write(note) / recall(policy) / list_notes()`
- `SkillManifest(name, description, entrypoint, references, scripts)`
- `SkillLoader.load(path) -> SkillManifest` (reads SKILL.md frontmatter; does not auto-read references)
- `SkillLoader.read_reference(manifest, relative_path) -> str` (explicit only; path traversal safe)

- [x] Implement + unit tests offline

### Task 2: Part 4 code — delegation

**Files:**
- Create: `packages/langchain_course/src/langchain_course/delegation.py`
- Create: `packages/langchain_course/tests/test_delegation.py`

**Interfaces:**
- `WorkerRole(name, system_prompt, max_steps, tool_names: list[str])`
- `WorkerTask(task_id, role, objective, context_messages: list[str], metadata)`
- `WorkerBudget(max_workers, max_steps_per_worker, max_total_steps)`
- `WorkerResult(task_id, status, final_text, steps, step_count, error_message)`
- `MergeResult(decisions, unresolved_conflicts, summary)`
- `DelegationCoordinator.run_task(task, budget, runner) / run_many(...)`
- Parent trail steps: `delegate_start`, `delegate_finish`, optional `delegate_error`
- Child prompt compiled from task objective + allowed context only (not parent secrets)
- Budget: count child model_request steps; reject over budget

Runner protocol: callable `(task, tools) -> AgentRunResult` for unit tests with scripted agents; live path may use `run_tool_calling_agent`.

- [x] Implement + unit tests offline

### Task 3: Course materials Parts 3–4

**Files:**
- Create chapters/labs/solutions 03 and 04 under `course/tracks/langchain/`
- Update README progress + handwritten-mapping.md
- Sync indexes / progress / roadmap

- [x] Materials + indexes

### Task 4: Verify, complete, push

```bash
uv run pytest packages/langchain_course/tests -q
uv run pytest -q
uv run ruff check .
uv run pytest tests/course/test_docs_freshness.py -q
```

- [x] Mark phase complete; commit; push; stop before F3 unless user continues full LC

# Multi-Agent and Delegation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first multi-agent runtime layer: role policies, isolated child task contexts, delegation events, budget accounting, merge contracts, an A2A adapter stub, and multi-agent eval cases.

**Architecture:** Phase 4 introduces `research_core.delegation` as a deterministic, offline-first layer above the Agent Kernel, Memory, Skills, and Research Core contracts. Child agents run through a small runner protocol so tests can use `AgentRunner` and `FakeModel` without provider SDKs. The runtime emits parent `delegate_*` events and embeds child event records as `delegate_event` payloads instead of mixing child messages into parent context.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, enums, pathlib-free core contracts, strict JSON-compatible metadata.

---

## File Structure

Create or update these files:

- Create: `redesign/packages/research_core/src/research_core/delegation/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/delegation/contracts.py`
- Create: `redesign/packages/research_core/src/research_core/delegation/runtime.py`
- Create: `redesign/packages/research_core/src/research_core/delegation/a2a.py`
- Create: `redesign/tests/research_core/test_delegation_contracts.py`
- Create: `redesign/tests/research_core/test_delegation_runtime.py`
- Create: `redesign/tests/research_core/test_delegation_a2a.py`
- Create: `redesign/tests/research_core/test_multi_agent_evals.py`
- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/architecture/data-model.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/README.md`
- Modify: `redesign/AGENTS.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-4.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy `app/`, `frontend/`, root `tests/`, root `eval`, provider SDK code, or product app placeholders.

## Contracts

### Delegation Contracts

- `AgentRolePolicy`: child-agent role boundary with `id`, `name`, `system_prompt`, scoped `tool_names`, scoped `skill_names`, allowed `memory_kinds`, and `max_steps`.
- `DelegationTask`: immutable parent-to-child assignment with `id`, `parent_run_id`, `child_run_id`, `objective`, role policy, optional isolated context messages, and metadata.
- `DelegationBudget`: local accounting policy with `max_child_runs`, `max_steps_per_child`, and `max_total_steps`.
- `DelegationResult`: child result wrapper with task, status, final message, child events, parent delegation events, error message, and step count.
- `DelegationMergeResult`: deterministic merge record built from accepted child results and failed/conflicting child results.

Child context messages must not include system messages. The role policy owns the child system prompt.

### Delegation Runtime

- `DelegationRuntime.run_task(task, budget)` emits `delegate_start`, `delegate_event`, and `delegate_finish` parent events.
- Child event records are embedded as `delegate_event` payloads with `task_id` and `child_run_id`.
- Child failures become observable failed `DelegationResult` records instead of silently disappearing.
- `DelegationRuntime.run_many(tasks, budget)` validates child-count and step budgets before returning stable task-order results.

This phase creates deterministic multi-agent orchestration contracts. True async execution, cancellation propagation, remote worker transport, and UI surfaces are deferred.

### A2A Adapter Stub

- `A2AEnvelope` serializes a `DelegationTask` into a remote-agent-ready record.
- `A2AAdapterStub.export_task(task)` returns a deterministic envelope.
- `A2AAdapterStub.send(envelope)` raises `NotImplementedError` with an explicit transport-not-implemented message.

### Eval Cases

- Child context isolation eval: child context receives role prompt and task context only, not parent history.
- Budget eval: over-budget child plans are rejected deterministically.
- Merge eval: failed child results remain visible as unresolved conflicts.

## Task 1: Add Phase 4 Plan and Start Progress

**Files:**

- Create: `redesign/docs/plans/2026-06-26-phase-4-multi-agent-delegation.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-4.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this Phase 4 plan**

Save this plan at `redesign/docs/plans/2026-06-26-phase-4-multi-agent-delegation.md`.

- [x] **Step 2: Mark Phase 4 as active**

Update the progress dashboard so Phase 4 is in progress and the verification baseline records the Phase 3 final baseline before Phase 4 changes.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "phase-4-multi-agent-delegation|Phase 4|DelegationRuntime|AgentRolePolicy|A2AAdapterStub" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: the Phase 4 plan and active progress state are discoverable from the docs index, roadmap, and progress dashboard.

## Task 2: Add Delegation Contracts

**Files:**

- Create: `redesign/packages/research_core/src/research_core/delegation/__init__.py`
- Create: `redesign/packages/research_core/src/research_core/delegation/contracts.py`
- Create: `redesign/tests/research_core/test_delegation_contracts.py`
- Modify: `redesign/docs/progress/phases/phase-4.md`

- [x] **Step 1: Write failing tests**

Create tests for:

- `AgentRolePolicy` rejects blank identifiers, blank prompts, blank scoped tool/skill names, and invalid `max_steps`;
- `DelegationTask` rejects blank identifiers/objectives and system messages in child context;
- `DelegationBudget` rejects invalid child and step limits;
- metadata and sequence fields are copied and immutable;
- merge results preserve child task order and expose failed child results as unresolved conflicts.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_contracts.py -q
```

Expected: failure because `research_core.delegation` does not exist.

- [x] **Step 3: Implement contracts**

Create immutable dataclasses and enums in `contracts.py`. Reuse runtime immutability helpers for metadata and event record copies.

- [x] **Step 4: Export contracts**

Update `research_core.delegation.__init__` to export all public Phase 4 delegation contracts.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_contracts.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_contracts.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 3: Add Delegation Runtime

**Files:**

- Create: `redesign/packages/research_core/src/research_core/delegation/runtime.py`
- Create: `redesign/tests/research_core/test_delegation_runtime.py`
- Modify: `redesign/packages/research_core/src/research_core/delegation/__init__.py`
- Modify: `redesign/docs/progress/phases/phase-4.md`

- [x] **Step 1: Write failing tests**

Create tests for:

- `run_task()` emits `delegate_start`, one `delegate_event` per child event, and `delegate_finish`;
- child final messages and child events are preserved in `DelegationResult`;
- child context isolation sends only the role system prompt and the task prompt to the child runner;
- child failures are returned as failed results with observable error and finish events;
- `run_many()` rejects too many child tasks and total child step budget overruns.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_runtime.py -q
```

Expected: failure because delegation runtime behavior is not implemented.

- [x] **Step 3: Implement runtime**

Create `DelegationRuntime` around a child runner factory protocol. Use existing `AgentRunResult`, `RunEvent`, `RunEventType`, and trajectory records.

- [x] **Step 4: Export runtime**

Update `research_core.delegation.__init__`.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_runtime.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_runtime.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 4: Add A2A Stub and Multi-Agent Eval Cases

**Files:**

- Create: `redesign/packages/research_core/src/research_core/delegation/a2a.py`
- Create: `redesign/tests/research_core/test_delegation_a2a.py`
- Create: `redesign/tests/research_core/test_multi_agent_evals.py`
- Modify: `redesign/packages/research_core/src/research_core/delegation/__init__.py`
- Modify: `redesign/docs/progress/phases/phase-4.md`

- [ ] **Step 1: Write failing tests**

Create tests for:

- A2A envelopes serialize task, role, objective, scope, and context message IDs;
- the adapter stub rejects send attempts with a clear not-implemented message;
- isolation eval catches accidental parent-history leakage;
- merge eval keeps failed child results as unresolved conflicts.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py -q
```

Expected: failure because A2A and eval behavior are not implemented.

- [ ] **Step 3: Implement A2A stub and eval helpers**

Keep the adapter local and deterministic. Do not add network transport or protocol dependencies.

- [ ] **Step 4: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py
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
- Modify: `redesign/docs/progress/phases/phase-4.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Update runtime architecture**

Document delegation runtime, child context isolation, budget accounting, merge contracts, and the A2A stub boundary.

- [ ] **Step 2: Update data model and glossary**

Add `AgentRolePolicy`, `DelegationTask`, `DelegationBudget`, `DelegationRuntime`, `DelegationResult`, `DelegationMergeResult`, and `A2AAdapterStub`.

- [ ] **Step 3: Update root docs and progress**

Mark Phase 4 complete only after final verification passes.

- [ ] **Step 4: Verify docs**

Run:

```bash
rg -n "DelegationRuntime|AgentRolePolicy|DelegationTask|DelegationBudget|DelegationMergeResult|A2AAdapterStub|child context isolation" redesign/docs redesign/README.md redesign/AGENTS.md
```

Expected: Phase 4 concepts are discoverable from docs, architecture, glossary, and progress.

## Task 6: Final Phase 4 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-4.md`

- [ ] **Step 1: Run full verification**

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

- [ ] **Step 2: Clean generated side effects**

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, and any `__pycache__` directories unless an approved plan adds them as tracked artifacts.

- [ ] **Step 3: Commit and push**

Commit with a message that records the Phase 4 deliverables and verification commands. Push branch `codex/redesign-phase-4`.

## Phase 4 Completion Checklist

- [ ] Delegation contracts are implemented and exported.
- [ ] Delegation contract tests pass.
- [ ] Delegation runtime emits parent delegation events and embeds child event records.
- [ ] Delegation runtime tests pass.
- [ ] Budget accounting and child context isolation eval cases pass.
- [ ] A2A adapter stub is implemented and tested.
- [ ] Merge contract exposes failed child results as unresolved conflicts.
- [ ] Architecture, glossary, README, AGENTS, roadmap, and progress docs are updated.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] `git diff --check` is clean.
- [ ] No legacy `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.

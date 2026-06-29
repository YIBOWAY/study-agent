# Phase 4 Progress: Multi-Agent and Delegation

Status: Complete

Started: 2026-06-26
Completed: 2026-06-26
Branch: `codex/redesign-phase-4`

## Goal

Add delegation runtime, isolated child context, role policies, budget accounting, merge contracts, and A2A adapter stub.

## Start Conditions

- Phase 3 memory and skill policies are stable.
- Runtime events can represent child-agent work without polluting parent context.

## Planned Deliverables

- Phase 4 executable plan under `redesign/docs/plans/`.
- `AgentRolePolicy`, `DelegationTask`, `DelegationBudget`, and merge contracts.
- `DelegationRuntime` that emits parent delegation events and embeds child event records.
- Child context isolation and budget accounting eval cases.
- A2A adapter stub for future remote-agent transport.
- Architecture docs, glossary, root README, AGENTS, roadmap, and progress updates.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-26 | Phase 4 started from Phase 3 baseline. Verification before changes: `uv run pytest -q` -> `116 passed`; `uv run ruff check .` -> `All checks passed!`. |
| 2026-06-26 | Task 2 delegation contracts added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_contracts.py -q` -> import error, `ModuleNotFoundError: No module named 'research_core.delegation'`. Green check: `uv run pytest tests/research_core/test_delegation_contracts.py -q` -> `9 passed`; `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_contracts.py` -> `All checks passed!`. |
| 2026-06-26 | Task 2 review fixes added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_contracts.py -q` -> `5 failed, 9 passed` for scoped sequence validation, message metadata validation, event run-id validation, and incomplete merge conflicts. Green check: `uv run pytest tests/research_core/test_delegation_contracts.py -q` -> `14 passed`; `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_contracts.py` -> `All checks passed!`. |
| 2026-06-26 | Task 3 delegation runtime added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> import error, `ImportError: cannot import name 'DelegationRuntime' from 'research_core.delegation'`. Green check: `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> `7 passed`; `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_runtime.py` -> `All checks passed!`. |
| 2026-06-26 | Task 3 review fixes added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> `6 failed, 6 passed` for observed child step budget enforcement, invalid exception event handling, duplicate delegation identifiers, and sequential total budget preflight. Green check: `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> `12 passed`; `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_runtime.py` -> `All checks passed!`; `git diff --check` -> clean. |
| 2026-06-26 | Task 3 exception-event hardening added after re-review. Red check: `uv run pytest tests/research_core/test_delegation_runtime.py::test_run_task_ignores_exception_events_iterables_that_raise -q` failed because a broken `exc.events` iterator masked the original child failure. Green check: the focused regression passed, `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> `13 passed`, and scoped `ruff` was clean. |
| 2026-06-26 | Task 3 exception-property hardening added after final re-review. Red check: `uv run pytest tests/research_core/test_delegation_runtime.py::test_run_task_ignores_exception_events_properties_that_raise -q` failed because reading a broken `exc.events` property masked the original child failure. Green check: exception-event regressions passed, `uv run pytest tests/research_core/test_delegation_runtime.py -q` -> `14 passed`, and scoped `ruff` was clean. |
| 2026-06-26 | Task 4 A2A stub and multi-agent eval cases added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py -q` -> collection error, `ImportError: cannot import name 'A2AAdapterStub' from 'research_core.delegation'`. Green check: same targeted pytest -> `5 passed`; `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py` -> `All checks passed!`; `git diff --check` -> clean. |
| 2026-06-26 | Task 4 A2A/eval review fixes added with TDD. Red check: `uv run pytest tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py -q` -> `5 failed, 3 passed` for missing A2A schema fields, duplicate context-message ID acceptance, and task metadata leakage. Green check: same targeted pytest -> `8 passed`; review-fix verification: `uv run ruff check packages/research_core/src/research_core/delegation tests/research_core/test_delegation_a2a.py tests/research_core/test_multi_agent_evals.py` -> `All checks passed!`; `git diff --check` -> clean. |
| 2026-06-26 | Phase 4 docs synchronized: runtime architecture, data model, glossary, docs index, root README, AGENTS instructions, roadmap, and progress docs now reflect Multi-Agent and Delegation. Initial Phase 4 verification: `uv run pytest -q` -> `152 passed`; `uv run ruff check .` -> `All checks passed!`; `git diff --check` clean. |
| 2026-06-26 | Post-phase audit catch-up added Chapter/Lab/Solution 02-04 so Research Core, Memory and Skills, and Multi-Agent Delegation are no longer code-only phases. It also fixed the Phase 2 branch-name docs error, added direct immutability tests, added AgentRunner multi-tool and exact-budget tests, added A2A envelope validation tests, exported `UnknownToolError`, clarified legacy vs redesign phase tables, and removed the temporary audit document. Verification: `uv run pytest -q` -> `160 passed`; `uv run ruff check .` -> `All checks passed!`; `git diff --check` clean. |
| 2026-06-29 | Post-phase review remediation accepted the explicit `DelegationMergeResult.unresolved_conflicts` validation finding and rejected the `run_many` total-budget finding as intentional fail-fast behavior already covered by tests. The fix rejects completed explicit conflicts and conflicts outside the merge decisions, and clarifies that `A2AAdapterStub` intentionally omits parent-private task metadata. Combined review verification: focused review suite -> `39 passed`; full `uv run pytest -q` -> `185 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`. |

## Delivered Files

- `packages/research_core/src/research_core/delegation/__init__.py`
- `packages/research_core/src/research_core/delegation/contracts.py`
- `packages/research_core/src/research_core/delegation/runtime.py`
- `packages/research_core/src/research_core/delegation/a2a.py`
- `tests/research_core/test_delegation_contracts.py`
- `tests/research_core/test_delegation_runtime.py`
- `tests/research_core/test_delegation_a2a.py`
- `tests/research_core/test_multi_agent_evals.py`

## Next Focus

Phase 5 planning: FastAPI product API, React workbench, runtime timeline, delegation tree, source/evidence panels, report editor, memory, skills, and eval panels.

## Verification Target

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

Recorded final result on 2026-06-26:

- `160 passed`
- `All checks passed!`
- `git diff --check` clean

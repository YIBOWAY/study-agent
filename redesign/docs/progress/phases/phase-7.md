# Phase 7 Progress: Production Readiness

Status: Complete

Started: 2026-06-30
Completed: 2026-06-30
Branch: `codex/redesign-phase-6`

## Goal

Add observability, persistence hardening, approval policy, sandbox policy, deployment docs, and docs freshness checks.

## Start Conditions

- Product and framework comparison phases have produced stable runtime and product contracts.
- Deployment and operations requirements are explicit.

## Planned Deliverables

- Phase 7 executable plan under `redesign/docs/plans/`.
- Offline production-readiness contracts for observability diagnostics, JSONL
  event persistence, approval policy, and sandbox policy.
- Docs freshness checks under `infra/` with tests.
- Deployment and operations docs.
- Course Chapter/Lab/Solution 07.
- README, AGENTS, architecture docs, glossary, course roadmap, docs index, and
  progress sync.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-30 | Phase 7 started with a first-principles course-mission audit and code graph architecture review. The plan now constrains production readiness to offline, inspectable contracts rather than real cloud/auth/database work. Code graph baseline: 57 indexed files, 898 nodes, 2,483 edges, index up to date. |
| 2026-06-30 | Task 2 added offline production-readiness contracts under `research_core.production`: `RunDiagnostics` for event observability, `JsonlRunEventStore` for append-only JSONL event persistence, and approval/sandbox policy decisions. Red check: focused production tests failed with `ModuleNotFoundError: No module named 'research_core.production'`. Green check: focused production pytest -> `11 passed`; scoped `ruff check` -> `All checks passed!`; `codegraph sync .` indexed the new production nodes. |
| 2026-06-30 | Task 3 added the docs freshness gate and local readiness docs. Red check: `uv run pytest tests/course/test_docs_freshness.py -q` failed with `ModuleNotFoundError: No module named 'infra.docs_freshness'`. Green check: docs freshness pytest -> `3 passed`; scoped `ruff check infra/docs_freshness.py tests/course/test_docs_freshness.py` -> `All checks passed!`; freshness probe confirmed `docs/operations/production-readiness.md` and `infra/local-readiness-checklist.md` are indexed. |
| 2026-06-30 | Task 4 added Course Chapter/Lab/Solution 07 for Production Readiness and synchronized course/docs indexes. The lesson teaches observability, JSONL event persistence, approval policy, sandbox policy, and docs freshness as offline contracts rather than cloud setup. |
| 2026-06-30 | Phase 7 completed after neat-freak docs reconciliation. Final verification: `uv run pytest -q` -> `199 passed`; `uv run ruff check .` -> `All checks passed!`; `npm install && npm run build` in `apps/web` -> Vite build passed with `46 modules transformed`; docs freshness gate confirmed Course 07, operations docs, and infra checklist paths are indexed; `git diff --check` clean. Generated `.venv`, caches, `uv.lock`, `node_modules`, `dist`, TypeScript build info, and Python `__pycache__` outputs were removed before final commit. |

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm install && npm run build
git diff --check
```

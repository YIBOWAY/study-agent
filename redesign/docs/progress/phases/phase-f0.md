# Phase F0 Progress: LangChain / LangGraph Parallel Track Scaffold

Status: Complete

Started: 2026-07-10  
Completed: 2026-07-10  
Branch: `codex/redesign-course-r7`

## Goal

Scaffold parallel LangChain and LangGraph teaching tracks: packages, optional deps, DeepSeek config, hello lab, indexes—without implementing Parts 1–7 or Capstone, and without breaking main offline CI.

## Start Conditions

- Handwritten teaching redesign R1–R9 complete
- Design approved: `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`
- Plan: `docs/plans/2026-07-10-phase-f0-langchain-langgraph-scaffold.md`

## Task Checklist

- [x] Task 1: Package skeletons + DeepSeek config + pyproject + AGENTS
- [x] Task 2: Chat factory + hello lab + track READMEs
- [x] Task 3: Index sync + docs freshness
- [x] Task 4: Mark complete, baseline, push

## Exit Signal

- [x] `packages/langchain_course` config unit tests green without API key
- [x] Optional langchain-course dependency group documented and installable
- [x] Track entrypoints under `course/tracks/{langchain,langgraph}/`
- [x] Main suite still green offline; integration tests skip by default
- [x] Indexes link tracks without claiming Parts 1–7 complete

## Verification (2026-07-10)

```text
uv sync --group langchain-course
uv run pytest packages/langchain_course/tests -q  → 4 passed, 1 skipped
uv run pytest -q                                 → 215 passed
uv run ruff check .                              → All checks passed!
uv run pytest tests/course/test_docs_freshness.py -q → 3 passed
```

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-10 | Phase F0 started. |
| 2026-07-10 | Packages, DeepSeek hello, track READMEs, optional groups, indexes landed. |
| 2026-07-10 | Verification green; phase marked Complete. Do not start F1 until user asks. |

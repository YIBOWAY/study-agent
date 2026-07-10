# Phase F1 Progress: LangChain Parts 1–2

Status: Complete

Started: 2026-07-10  
Completed: 2026-07-10  
Branch: `codex/redesign-course-r7`

## Goal

Deliver LangChain track Parts 1–2 (tool-calling agent kernel + research evidence chain) with `.env` DeepSeek loading, offline unit tests, and course materials—without `research_core` mix or main CI breakage.

## Start Conditions

- F0 complete (`docs/progress/phases/phase-f0.md`)
- Design: `docs/specs/2026-07-10-langchain-langgraph-parallel-tracks-design.md`
- Plan: `docs/plans/2026-07-10-phase-f1-langchain-parts-1-2.md`

## Task Checklist

- [x] Task 1: `.env` support + ignore + example + docs
- [x] Task 2: Part 1 agent kernel code + unit tests
- [x] Task 3: Part 2 research evidence chain code + unit tests
- [x] Task 4: Course chapters/labs/solutions + mapping
- [x] Task 5: Indexes, verification, complete, push

## Exit Signal

- [x] `.env` load works; real keys never committed
- [x] Part 1 unit tests green offline (plain + tool loop)
- [x] Part 2 unit tests green offline (retrieve + claim links)
- [x] Track materials for Parts 1–2 present and indexed
- [x] Main suite still offline green

## Verification (2026-07-10)

```text
uv sync --group langchain-course
uv run pytest packages/langchain_course/tests -q  → unit pass, integration skipped
uv run pytest -q                                 → main offline green
uv run ruff check .                              → clean
uv run pytest tests/course/test_docs_freshness.py -q → green
```

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-10 | Phase F1 started. |
| 2026-07-10 | `.env` loading, Parts 1–2 code/tests/materials, indexes landed; phase Complete. |

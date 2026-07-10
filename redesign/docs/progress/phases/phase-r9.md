# Phase R9 Progress: Course Teaching Redesign - Reference & Support Materials

Status: Complete

Started: 2026-07-10  
Completed: 2026-07-10  
Branch: `codex/redesign-course-r7`

## Goal

Author reference and support materials for the project-driven course: common patterns, troubleshooting, design-decision index, discussion prompts with detailed answers, and glossary expansion.

## Start Conditions

- Runtime/product phases 0–7 complete
- Teaching redesign R1–R8 complete (Capstone full materials under `course/capstone/`)
- Post-R8 honesty fixes landed (`7fd8aa4`)
- R9 listed as planned in teaching redesign spec and course indexes

## Task Checklist

- [x] Task 1: Start R9 plan and progress
- [x] Task 2: Finish inventory of DD/TRAP/terms
- [x] Task 3: Author reference materials + glossary + discussion answers
- [x] Task 4: Index sync, verification, mark complete, commit/push

## Exit Signal

- [x] Reference materials complete and offline-readable
- [x] Discussion prompts include detailed 参考答案与解析
- [x] Indexes no longer list R9 as planned-only
- [x] Verification baseline recorded

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-10 | Phase R9 started. Plan at `docs/plans/2026-07-10-phase-r9-course-teaching-redesign.md`. |
| 2026-07-10 | Authored `course/reference/common-patterns.md`, `course/reference/troubleshooting.md`, `course/reference/design-decisions-index.md`, `course/reference/discussion-prompts.md` (with detailed answers), expanded `course/reference/agent-kernel-glossary.md`. |
| 2026-07-10 | Index sync across course/docs/progress; R9 marked complete; verification + commit/push. |

## Deliverables

- `course/reference/common-patterns.md`
- `course/reference/troubleshooting.md`
- `course/reference/design-decisions-index.md`
- `course/reference/discussion-prompts.md`
- `course/reference/agent-kernel-glossary.md` (expanded)
- `docs/plans/2026-07-10-phase-r9-course-teaching-redesign.md`
- Index sync across course/README, docs/course/roadmap, docs/README, progress overall/README, execution roadmap, teaching redesign status

## Verification Target

```bash
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run pytest -q
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run ruff check .
PYTHONPATH=packages/research_core/src UV_CACHE_DIR=$TMPDIR/uv-cache-r9 uv run pytest tests/course/test_docs_freshness.py -q
```

## Verification Results

- Full suite under `tests/`: `215 passed`
- `ruff check .`: clean
- Docs freshness: `3 passed`
- Capstone: `2 passed, 1 skipped` (`solution` green; `starter` skip until implemented)

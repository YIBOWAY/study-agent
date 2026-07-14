# Phase F3 Progress: LangChain Parts 5–7 + Capstone

Status: Complete

Started: 2026-07-14  
Completed: 2026-07-14  
Branch: `codex/redesign-course-r7`

## Goal

Deliver LangChain track Parts 5–7 and Capstone with offline unit tests and course materials—without `research_core` mix or main CI breakage.

## Task Checklist

- [x] Task 1: Workbench code/tests
- [x] Task 2: Comparisons code/tests
- [x] Task 3: Production code/tests
- [x] Task 4: Course materials Parts 5–7
- [x] Task 5: LC Capstone
- [x] Task 6: Indexes, verify, complete, push

## Delivered

### Code (`packages/langchain_course`)

- `workbench.py`: nine-panel `WorkbenchSnapshot`, `from_step` / domain adapters, referential integrity
- `comparisons.py`: weighted `FrameworkProfile` matrix, `run_lc_baseline`, default profiles
- `production.py`: `RunDiagnostics.from_steps`, `JsonlStepStore`, `ApprovalPolicy`, `SandboxPolicy`
- Tests: `test_workbench.py`, `test_comparisons.py`, `test_production.py`

### Course (`course/tracks/langchain`)

- Chapters / labs / solutions 05–07
- Capstone under `capstone/` (fixtures, skill, starter, solution, rubric)
- README path + progress F3 complete
- `reference/handwritten-mapping.md` through Capstone

### Indexes

- `course/README.md`, `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/overall.md`, design status F0–F3

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-14 | Phase F3 started after F2 re-verify (215 passed, ruff clean). |
| 2026-07-14 | Parts 5–7 modules/tests/materials + Capstone; indexes synced; verification green; phase complete. |

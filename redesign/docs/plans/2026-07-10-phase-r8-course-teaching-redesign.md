# Phase R8: Capstone Project Implementation Plan


**Status:** Complete (2026-07-10)
> **For agentic workers:** implement task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the Capstone placeholder with a complete offline 本地论文研究助手 project under `course/capstone/`: product-style README, rubric, paper fixtures, starter skeleton, runnable solution, event trajectory, sample report, and design reflection. Sync course/docs indexes so learners can treat Capstone as a real final project after Parts 1-7.

**Architecture:** Teaching artifacts only under `course/capstone/`. No product-path changes to `packages/research_core`, `apps/api`, or `apps/web` unless a verified contract bug blocks Capstone honesty. Capstone solution composes public APIs already taught in Parts 1-7:

```text
paper_fixtures/*.json
      |
      v
SourceIngestor + FakeRetriever
      |
      +--> Evidence / Claim / Report / ClaimSourceLink
      |
      +--> MemoryEngine + SkillRuntime
      |
      +--> DelegationRuntime (optional child review)
      |
      +--> AgentRunner + FakeModel tool trail
      |
      +--> WorkbenchSnapshot.to_record()
      |
      +--> RunDiagnostics + JsonlRunEventStore + Approval/Sandbox decisions
```

**Tech Stack:** Markdown, JSON fixtures, Python teaching code under `course/capstone/`, pytest for starter/solution tests, existing docs freshness and (optional) course tests.

---

## First-Principles Review

R1-R7 rewrote the course into a project-driven path ending at Capstone. The current `course/capstone/README.md` is still an R1 placeholder: it tells learners not to treat it as requirements, starter, or solution. That blocks the course promise: "integrate all Parts into a complete offline paper research assistant."

Success criteria from the teaching redesign spec:

1. Extract evidence from at least 3 sources (local paper fixtures).
2. Every report claim traces to evidence.
3. Use at least 1 skill and 1 memory policy.
4. Timeline is visible in a Workbench snapshot record.
5. Capstone tests pass offline with `uv run pytest`.
6. Reflection explains 3 key design decisions.

R8 also absorbs residual course polish from the post-R7 review:

- Keep Capstone honest about declarative vs wired contracts (role `skill_names`/`memory_kinds`, MEMORY/SKILL events, `max_runtime_seconds` via `runtime_decision`).
- Prefer portable paths and offline-only fixtures.
- Do not commit `node_modules/`, `tsconfig.tsbuildinfo`, or `uv.lock` unless locking is intentional.

## Global Constraints

- Keep Capstone offline: static paper fixtures, `FakeModel`, `FakeRetriever`, no network, no provider SDKs, no API keys.
- Capstone starter/solution live under `course/capstone/`; they are course artifacts, not product modules.
- Do not import third-party agent frameworks into Capstone.
- Prefer public `research_core` exports already taught in Parts 1-7.
- Update indexes that still say "Capstone placeholder / planned R8".
- Leave R9 (reference/support materials) planned unless a Capstone dependency forces a tiny glossary/link update.

## File Map

Create:

- `docs/plans/2026-07-10-phase-r8-course-teaching-redesign.md` (this file)
- `docs/progress/phases/phase-r8.md`
- `course/capstone/rubric.md`
- `course/capstone/paper_fixtures/papers.json`
- `course/capstone/paper_fixtures/README.md`
- `course/capstone/starter/agent_starter.py`
- `course/capstone/starter/test_starter.py`
- `course/capstone/solution/agent.py`
- `course/capstone/solution/test_run.py`
- `course/capstone/solution/trajectory.jsonl`
- `course/capstone/solution/report.md`
- `course/capstone/solution/reflection.md`
- `course/capstone/skills/citation-check/SKILL.md`
- `course/capstone/skills/citation-check/references/citation-rules.md`
- `.gitignore` (repo hygiene residual)

Modify:

- `course/capstone/README.md` — full product-style Capstone brief
- `course/README.md`
- `README.md`
- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `docs/specs/2026-06-30-course-teaching-redesign.md` status wording if needed
- `course/chapters/07-production-readiness.md` Capstone checklist line only if still "planned"

## Task 1: Start R8 Plan And Progress

- [x] Write this plan and `docs/progress/phases/phase-r8.md`.
- [x] Mark R8 active in overall/progress indexes without claiming Capstone complete.
- [x] Link the plan from docs indexes.

## Task 2: Paper Fixtures + Rubric + README

- [x] Ship offline paper fixtures (>=3 papers) with stable URIs and citation-friendly content.
- [x] Write rubric with the 6 success criteria and scoring guidance.
- [x] Rewrite Capstone README as a real project brief: problem, constraints, deliverables, workflow, honesty notes.

## Task 3: Starter Skeleton

- [x] Provide `agent_starter.py` with TODOs that force learners to compose Parts 1-7.
- [x] Provide `test_starter.py` with failing/skipped or assert-driven scaffold that becomes green when solution shape is filled.

## Task 4: Reference Solution + Artifacts

- [x] Implement `solution/agent.py` end-to-end offline assistant.
- [x] Implement `solution/test_run.py` covering rubric criteria.
- [x] Generate `trajectory.jsonl`, sample `report.md`, and `reflection.md`.
- [x] Include a citation skill package under Capstone for SkillRuntime loading.

## Task 5: Residual Optimization

- [x] Add root `.gitignore` for local artifacts (`node_modules`, caches, lockfiles not intended for commit).
- [x] Sweep index wording that still treats Capstone as placeholder after materials land.
- [x] Preserve honesty about declarative role fields and non-auto MEMORY/SKILL events.

## Task 6: Docs Sync + Verification

- [x] Sync course/docs/progress/README surfaces.
- [x] Run pytest, ruff, docs freshness; run Capstone solution tests.
- [x] Record verification in phase-r8 progress and overall baseline.

## Exit Signal

- Capstone is no longer a placeholder.
- Learners can complete the project offline with fixtures + starter + rubric.
- Solution proves all 6 success criteria.
- Indexes and progress mark R8 complete; R9 remains planned.

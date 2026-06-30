# Phase 7 Plan: Production Readiness

Date: 2026-06-30

## First-Principles Review

The redesign goal has not changed: this project is a course first, an engineering
reference second, and a product portfolio piece third. Phase 7 must not turn the
project into an infra-first deployment exercise. It should teach production
readiness as inspectable, offline-testable contracts before any real cloud,
database, auth, or provider dependency is introduced.

Current review findings:

- The course path is still sensible: primer, glossary, Chapter/Lab/Solution 00,
  then Chapters 01-06 in dependency order.
- Phase 7 was only a roadmap stub before this plan. Starting implementation
  without a plan would violate the redesign planning rule.
- Production readiness can easily drift into vague ops checklists. This phase
  must instead create small, executable contracts that a learner can run,
  inspect, break, and repair.
- The Knowledge and Deep Research slice is still explicitly deferred. Phase 7
  should not claim the whole 24-week course is complete.
- Code graph review confirms the current seams: `research_core.runtime` owns
  `RunEvent` and trajectories, `research_core.product` adapts domain/runtime
  records into `WorkbenchSnapshot`, `apps/api` is transport-only, and `apps/web`
  consumes the product record shape.

## Goal

Add the first production-readiness layer while preserving the teaching mission:
observability summaries, append-only persistence contracts, approval/sandbox
policy contracts, deployment/readiness docs, docs freshness checks, and Course
07 material.

## Non-Goals

- No real cloud deployment.
- No real OAuth/auth provider.
- No real database migration layer.
- No live provider SDK dependency.
- No real A2A network transport.
- No production logic in `apps/api` beyond transport over product contracts.
- No separate React data model for production state.

## Planned Deliverables

1. Phase 7 plan and progress start records.
2. Production-readiness contracts under the offline `research_core` boundary:
   - run diagnostics from `RunEvent` trajectories,
   - append-only JSONL event persistence,
   - approval and sandbox policy decisions.
3. Docs freshness gate under `infra/` with tests that keep course and docs
   indexes aligned with existing files.
4. Deployment and operations documentation that explains local readiness,
   verification, artifact cleanup, and deferred real infrastructure.
5. Course Chapter/Lab/Solution 07 teaching production readiness as contracts,
   not as cloud setup.
6. Synchronized `README`, `AGENTS`, architecture docs, glossary, course roadmap,
   docs index, and progress docs.

## Implementation Tasks

### Task 1: Plan, Audit, and Course Path Alignment

- Record the first-principles audit in this plan.
- Start Phase 7 progress.
- Add this plan to the roadmap and docs index.
- Fix any small course-path inconsistency found during audit, including the
  missing Solution 00 mention in the beginner path.
- Commit and push this planning milestone.

### Task 2: Production Readiness Contracts

Use TDD first.

- Add observability diagnostics around `RunEvent` sequences.
- Add append-only JSONL persistence for run events with schema validation and
  deterministic readback.
- Add approval and sandbox policy objects that explain whether a tool/action is
  allowed, blocked, or requires human approval.
- Keep these contracts offline-first and independent from FastAPI, React,
  provider SDKs, and databases.
- Update focused tests before implementation and verify red/green.

### Task 3: Docs Freshness and Deployment Readiness

Use tests before implementation for freshness behavior.

- Add a docs freshness checker that validates course/docs indexes point at real
  files and that phase plan/progress surfaces stay aligned.
- Add deployment/readiness docs under `docs/` and `infra/`.
- Keep deployment docs local-first: how to run, verify, build, clean generated
  artifacts, and what remains deferred.

### Task 4: Course 07

- Add Chapter 07, Lab 07, and Solution 07.
- Teach production readiness in plain language:
  observability answers "what happened", persistence answers "what survives",
  approval/sandbox answers "what is allowed", freshness checks answer "can the
  docs be trusted".
- Include runnable offline examples and one deliberate failure case.
- Update `course/README.md` and `docs/course/roadmap.md`.

### Task 5: Final Reconciliation

- Run full verification:
  - `uv run pytest -q`
  - `uv run ruff check .`
  - `cd apps/web && npm install && npm run build`
  - `git diff --check`
- Clean generated artifacts: `.venv`, `uv.lock`, caches, `node_modules`, `dist`,
  TypeScript build info, and Python `__pycache__`.
- Run neat-freak-style docs reconciliation.
- Commit and push the final Phase 7 milestone.

## Verification Target

Run from `redesign/` unless noted:

```bash
uv run pytest -q
uv run ruff check .
cd apps/web && npm install && npm run build
git diff --check
```

## Exit Criteria

- Phase 7 production-readiness contracts are covered by offline tests.
- Docs freshness checks fail on missing indexed course/docs files.
- Deployment docs exist and explicitly separate local readiness from deferred
  real infrastructure.
- Course Chapter/Lab/Solution 07 exist and are linked from course indexes.
- Progress docs record start, implementation milestones, final verification, and
  cleanup.
- No generated artifacts are committed.

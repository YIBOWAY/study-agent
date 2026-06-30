# Phase R2: Part 2 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Part 2 so Research Core teaches the source -> evidence -> claim -> report chain through the local paper research assistant's citation problem, using the project-driven teaching contract established in Phase R1.

**Architecture:** No runtime/product code changes. R2 only rewrites `course/chapters/02-research-core-foundations.md`, `course/labs/02-source-evidence-claim-lab.md`, `course/solutions/02-source-evidence-claim-solution.md`, and the docs/progress surfaces that index them. The rewrite uses existing `research_core.research` contracts: `SourceInput`, `SourceIngestor`, `FakeRetriever`, `Evidence`, `Claim`, `Report`, and `build_claim_source_links`.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`.

---

## First-Principles Review

R1 completed the learner entrypoint and Part 1. The current Part 2 files are technically correct v1 material, but they still teach by listing objects first and only lightly exercising failure paths. The approved teaching redesign says Part 2 must start from the learner-facing problem: the assistant can now run, but a research answer is not trustworthy unless every claim can be traced back to evidence and source.

Therefore R2 should not add new code to `packages/` or `apps/`. The existing Research Core implementation is enough for the teaching rewrite. The phase succeeds when the Part 2 materials follow the R1 teaching rhythm:

- problem hook: "Agent 说的话找不到出处";
- detective-style evidence chain: Source = 案发现场, Evidence = 证物, Claim = 结论, Report = 案件陈述;
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop;
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops;
- at least two ASCII diagrams, including the data flow `SourceInput -> Source -> Evidence -> Claim -> Report -> ClaimSourceLink`;
- Workbench connection that explains why source/evidence/report records matter to product UI;
- offline verification only.

## Global Constraints

- Do not modify `packages/research_core`, `apps/api`, `apps/web`, or product/runtime tests in this phase.
- Do not introduce network calls, API keys, real paper databases, real embeddings, or live retrievers.
- Use existing local examples and deterministic fake retrieval only.
- Keep all snippets runnable from `redesign/`.
- Keep Parts 3-7 labeled as current v1 material until their own R3-R7 rewrites land.
- Update `docs/progress/` after each landed task or milestone.
- Commit and push each milestone with a detailed commit message.

## File Map

Create:

- `docs/plans/2026-07-01-phase-r2-course-teaching-redesign.md`
- `docs/progress/phases/phase-r2.md`

Modify:

- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `course/README.md`
- `course/chapters/02-research-core-foundations.md`
- `course/labs/02-source-evidence-claim-lab.md`
- `course/solutions/02-source-evidence-claim-solution.md`

## Task 1: Start R2 Plan And Progress

**Files:**

- Create: `docs/plans/2026-07-01-phase-r2-course-teaching-redesign.md`
- Create: `docs/progress/phases/phase-r2.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/README.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this plan**

Save this plan under `docs/plans/`.

- [x] **Step 2: Start progress tracking**

Create `docs/progress/phases/phase-r2.md` with R2 scope, task checklist, verification target, and a start log dated `2026-07-01`.

- [x] **Step 3: Update indexes**

Update docs/progress indexes so R2 is visible as active, without marking rewritten course content complete.

- [x] **Step 4: Verify indexed docs paths**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: docs freshness passes.

- [x] **Step 5: Commit and push**

Commit the plan/progress kickoff and push `codex/redesign-course-r2`.

## Task 2: Rewrite Chapter 02

**Files:**

- Modify: `course/chapters/02-research-core-foundations.md`
- Modify: `docs/progress/phases/phase-r2.md`

- [x] **Step 1: Rewrite opener and learner contract**

Turn Chapter 02 into "Part 2: Research Core" and start from the problem: the assistant can produce text, but researchers cannot trust claims without traceable evidence.

- [x] **Step 2: Add architecture and data-flow diagrams**

Include an architecture map showing Part 2 in the full local paper research assistant and a data-flow diagram from `SourceInput` to `ClaimSourceLink`.

- [x] **Step 3: Build the evidence chain**

Use a local paper fixture about RAG evaluation and citation mapping. Show `SourceIngestor`, `FakeRetriever`, `Evidence`, `Claim`, `Report`, and `build_claim_source_links` in a runnable snippet.

- [x] **Step 4: Inspect, modify, break, fix, reflect**

Teach learners to inspect source IDs, retrieval scores, link records, and explicit error messages. Include unsupported-claim and missing-evidence failure paths.

- [x] **Step 5: Add product connection and eval gate**

Explain how Workbench source/evidence/report panels use the records and list exact pytest/ruff commands.

## Task 3: Rewrite Lab 02

**Files:**

- Modify: `course/labs/02-source-evidence-claim-lab.md`
- Modify: `docs/progress/phases/phase-r2.md`

- [x] **Step 1: Convert lab to L1/L2/L3**

L1 builds the smallest evidence chain. L2 changes the fixture or query and predicts how ranking/link records change. L3 asks the learner to design a new local paper fixture and evidence-backed report.

- [x] **Step 2: Add feedback loops**

Every exercise must include Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct.

- [x] **Step 3: Add break/fix checks**

Include unsupported claim, missing evidence, and missing source scenarios with expected error interpretation.

## Task 4: Rewrite Solution 02

**Files:**

- Modify: `course/solutions/02-source-evidence-claim-solution.md`
- Modify: `docs/progress/phases/phase-r2.md`

- [x] **Step 1: Provide runnable answers**

Include complete L1/L2/L3 solution snippets and assertions.

- [x] **Step 2: Explain why answers are correct**

For each exercise, explain what the assertions prove and which misunderstanding they rule out.

- [x] **Step 3: Connect design decisions forward**

Explain why the evidence chain matters for Memory, Delegation, Workbench, and Production Diagnostics.

## Task 5: Sync Course Indexes And Progress

**Files:**

- Modify: `course/README.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r2.md`

- [x] **Step 1: Mark Part 2 as R2 rewritten**

After Tasks 2-4 land, update course indexes to describe Part 2 as completed R2 material. Keep Parts 3-7 as current v1 material.

- [x] **Step 2: Verify docs freshness**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: `3 passed`.

## Task 6: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r2.md`

- [x] **Step 1: Run final verification**

Run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [x] **Step 2: Clean generated artifacts**

Remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.

- [x] **Step 3: Run final docs reconciliation**

Use the neat-freak workflow to verify docs/progress/README/AGENTS alignment.

- [x] **Step 4: Mark R2 complete and push**

Only after fresh verification, mark R2 complete, commit the final docs sync, and push the branch.

## Exit Criteria

- Part 2 Chapter/Lab/Solution are rewritten around the citation problem.
- Lab 02 has L1/L2/L3 exercises with feedback loops.
- Solution 02 includes design rationale and why-correct explanations.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R2 status.
- No runtime/product code changes were needed.
- Final verification is recorded in `docs/progress/phases/phase-r2.md` and `docs/progress/overall.md`.

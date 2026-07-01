# Phase R3: Part 3 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Part 3 so Memory and Skills teach persistent memory policies and progressive-disclosure skill loading through the local paper research assistant's repeated-session problem, using the project-driven teaching contract established in Phase R1 and continued in Phase R2.

**Architecture:** No runtime/product code changes. R3 rewrites `course/chapters/03-memory-and-skills.md`, `course/labs/03-memory-skill-runtime-lab.md`, `course/solutions/03-memory-skill-runtime-solution.md`, and the docs/progress surfaces that index them. R3 also adds a narrow course-verification gate that extracts fenced `python` blocks from selected markdown files and executes them against the local `research_core` API. The rewrite uses existing `research_core.memory` and `research_core.skills` contracts: `MemoryRecord`, `MemoryKind`, `MemoryWritePolicy`, `MemoryRecallPolicy`, `MemoryEngine`, `SkillPackage`, and `SkillRuntime`.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`, plus pytest-backed markdown Python block execution under `infra/`.

---

## First-Principles Review

R2 completed the Part 2 teaching rewrite. The current Part 3 files (`chapters/03-memory-and-skills.md`, `labs/03-memory-skill-runtime-lab.md`, `solutions/03-memory-skill-runtime-solution.md`) are still v1 material. Reading them against the Part Contract in `docs/course/roadmap.md` shows concrete gaps, not just a style mismatch:

- No Problem Hook narrative. The chapter opens with a "Goal" section and a Core Objects table, not a concrete failure the researcher experiences.
- No mental-model analogy. The spec (`docs/specs/2026-06-30-course-teaching-redesign.md`, Phase R3 entry) calls for "Memory = Agent 的笔记本" and "Skills = Agent 的技能包"; the current chapter has neither.
- Only 2 of 6 `MemoryKind` values are ever demonstrated (`SEMANTIC`, `PINNED`). `WORKING`, `SESSION`, `EPISODIC`, and `PROCEDURAL` are never shown, so learners cannot see what problem the other kinds solve.
- `MemoryWritePolicy.max_content_chars` and `MemoryRecallPolicy.allowed_kinds` are never exercised anywhere in the chapter, lab, or solution, even though both are real fields on the contracts.
- `MemoryEngine.list_records()` is never used. Part 1 and Part 2 each teach an "inspect everything" habit (`events_to_records`, link records); Part 3 currently has no equivalent for memory state.
- `SkillRuntime` discovers `references/`, `scripts/`, and `assets/`, but the chapter and lab only ever demonstrate `references/`. The "skill package" concept is incompletely taught.
- Lab 03 has two flat "Exercise" blocks with expected output and a self-check assert, but no L1/L2/L3 tiering and no Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback loop for any exercise.
- The chapter's "Failure Lab Preview" shows two failures inline (forbidden phrase, path traversal) but they are not part of a tiered Break/Fix cycle with diagnosis questions.
- There are no ASCII diagrams anywhere in the current Part 3 material.
- There is no L3 "design a memory policy" exercise, which the approved spec explicitly calls for.
- `tests/course/test_docs_freshness.py` only validates indexed markdown paths. It does not execute course code blocks, so Part 3 examples can drift away from the real `research_core.memory` / `research_core.skills` API without CI noticing.
- The Part 3 rewrite must teach all six `MemoryKind` labels with one "when to use" sentence each. Source behavior only gives `PINNED` special recall ordering; the other kinds are strategy labels enforced by write/recall policies, not separate algorithms.
- The L3 design exercise must not pretend there is one canonical policy answer. The solution should provide one reference design plus required invariants, such as pinned rules outranking session notes and draft working memory never being recalled after a session.
- The memory recall diagram should expose the real deterministic sort key: `(pinned_rank, -score, index)`.
- The memory write-policy failure lab should teach the real short-circuit order: `kind` -> `importance` -> `forbidden_phrases` -> `max_content_chars`. If one record violates multiple rules, the first failing boundary is the reported error.

I verified the parts of the real `research_core.memory` and `research_core.skills` API that the current v1 material does not exercise, so the rewrite has accurate new material to draw on (all outputs below were confirmed by running the exact snippets from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`):

```python
# max_content_chars boundary
MemoryWritePolicy(allowed_kinds=[MemoryKind.SEMANTIC], max_content_chars=20).validate(
    MemoryRecord(id="long_1", kind=MemoryKind.SEMANTIC, content="x" * 21, importance=0.9)
)
# -> ValueError: content exceeds policy maximum

# allowed_kinds filter in recall
engine.recall(MemoryRecallPolicy(query="evidence", allowed_kinds=[MemoryKind.SEMANTIC], limit=5))
# -> only SEMANTIC records come back, even if a WORKING record also matches the query

# list_records as an inspection tool
engine.list_records()  # -> tuple of every MemoryRecord written so far, in write order

# skill scripts/assets discovery (not just references)
package.scripts  # -> ('scripts/run.py',)
package.assets   # -> ('assets/logo.png',)

# reading a reference that does not exist
runtime.read_reference(package, "references/missing.md")
# -> ValueError: reference file does not exist
```

Therefore R3 should not add new code to `packages/` or `apps/`. The existing Memory and Skills implementation already has enough surface area for a full Part Contract rewrite; the current material simply teaches a small slice of it. The only new code in scope is the course markdown Python block verification gate under `infra/` and `tests/course/`. The phase succeeds when Part 3 follows the same rhythm as Part 1 and Part 2:

- problem hook: "助手上次查过的东西，这次完全不记得,而且规则也没有跟着传下来";
- two mental models: Memory = 研究助手的笔记本（不是什么都值得记）, Skills = 研究助手的技能包（平时收在抽屉里，要用哪个能力才翻开哪部分资料）;
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop covering both memory and skills;
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops, including an L3 that asks the learner to design a new `MemoryWritePolicy`/`MemoryRecallPolicy` pair from a requirement, not just reuse the example;
- at least two ASCII diagrams, including a memory write/recall flow and a skill load/read-reference flow;
- a Workbench connection section explaining why memory and skill state must stay inspectable for the product panels planned in Part 5;
- an automated markdown Python block gate for the changed Part 3 code examples, so future R4-R9 rewrites are not protected only by manual copy/paste discipline;
- offline verification only.

## Global Constraints

- Do not modify `packages/research_core`, `apps/api`, `apps/web`, or product/runtime tests in this phase.
- The allowed code changes are limited to `infra/markdown_python_blocks.py` and `tests/course/test_markdown_python_blocks.py`.
- Do not introduce network calls, API keys, real databases, or a real skill marketplace.
- Use only the existing `research_core.memory` and `research_core.skills` contracts; do not add new fields or methods to them.
- Keep all snippets runnable from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`.
- Keep changed Part 3 fenced `python` snippets covered by the markdown Python block gate unless a snippet is deliberately non-executable and explicitly marked outside the gate's selected file list.
- Keep Parts 4-7 labeled as current v1 material until their own R4-R7 rewrites land.
- Update `docs/progress/` after each landed task or milestone.
- Commit and push each milestone with a detailed commit message.

## File Map

Create:

- `docs/plans/2026-07-01-phase-r3-course-teaching-redesign.md`
- `docs/progress/phases/phase-r3.md`
- `infra/markdown_python_blocks.py`
- `tests/course/test_markdown_python_blocks.py`

Modify:

- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `course/README.md`
- `course/chapters/03-memory-and-skills.md`
- `course/labs/03-memory-skill-runtime-lab.md`
- `course/solutions/03-memory-skill-runtime-solution.md`

## Task 1: Start R3 Plan And Progress

**Files:**

- Create: `docs/plans/2026-07-01-phase-r3-course-teaching-redesign.md`
- Create: `docs/progress/phases/phase-r3.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/README.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this plan**

Save this plan under `docs/plans/` (already done by this task's authoring step).

- [x] **Step 2: Start progress tracking**

Create `docs/progress/phases/phase-r3.md` with R3 scope, task checklist, verification target, and a start log dated with the actual start date.

- [x] **Step 3: Update indexes**

Update `docs/README.md`, `docs/progress/README.md`, `docs/progress/overall.md`, and `docs/plans/2026-06-25-redesign-execution-roadmap.md` so R3 is visible as active, without marking rewritten course content complete yet.

- [x] **Step 4: Verify indexed docs paths**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: docs freshness passes.

- [x] **Step 5: Commit**

Commit the plan/progress kickoff on a phase branch (for example `codex/redesign-course-r3`).

## Task 2: Add Markdown Python Block Verification Gate

**Files:**

- Create: `infra/markdown_python_blocks.py`
- Create: `tests/course/test_markdown_python_blocks.py`
- Modify: `docs/progress/phases/phase-r3.md`

- [x] **Step 1: Write failing tests first**

Add tests that prove the gate can extract fenced `python` blocks from markdown, execute blocks from the same file in a shared namespace, compare output when the markdown provides an `Expected output:` `text` block, report mismatches with file and line context, and import `research_core` through the same path boundary used by the course.

- [x] **Step 2: Implement the gate**

Implement a small parser/executor under `infra/markdown_python_blocks.py`. It should be offline-only, add `packages/research_core/src` to `sys.path` for execution, capture stdout per block, compare expected output only when an adjacent expected-output text fence is marked, and expose a CLI so humans can run the same check outside pytest.

- [x] **Step 3: Cover Part 3 course files**

Wire `tests/course/test_markdown_python_blocks.py` so the changed Part 3 chapter/lab/solution files are checked by pytest after the rewrite lands. The initial infra tests may use temporary markdown fixtures before the Part 3 files are rewritten.

- [x] **Step 4: Verify and commit**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
```

Expected: markdown Python block tests pass. Commit and push this infra milestone.

## Task 3: Rewrite Chapter 03

**Files:**

- Modify: `course/chapters/03-memory-and-skills.md`
- Modify: `docs/progress/phases/phase-r3.md`

- [ ] **Step 1: Rewrite opener and learner contract**

Turn Chapter 03 into "Part 3: Memory and Skills" with a Learner Contract block (Who this is for / Before you start / You will build / You will be able to explain / You will prove it works by running / Offline guarantee), matching the Chapter 02 shape.

- [ ] **Step 2: Open with the problem hook**

Start from the researcher asking a follow-up question in a new session. The assistant re-derives the same evidence chain from scratch and no longer applies a rule it was told last time (for example "always cite sources"). Name this "the assistant has no notebook" problem before introducing any object.

- [ ] **Step 3: Introduce the two mental models**

Memory = 研究助手的笔记本：不是什么都值得写进去，笔记本也需要能查、能优先看到重要规则。Skills = 研究助手的技能包：平时收在抽屉里，只有要用某个能力时才翻开对应资料，不会一次性把所有资料倒在桌上。Use a small story-role table like Chapter 01's, mapping `MemoryRecord` / `MemoryWritePolicy` / `MemoryRecallPolicy` / `MemoryEngine` and `SkillPackage` / `SkillRuntime` to their plain-language roles. Add a `MemoryKind` mental-model table with one "when to use" sentence for each of `WORKING`, `SESSION`, `EPISODIC`, `SEMANTIC`, `PROCEDURAL`, and `PINNED`, and explicitly note that only `PINNED` has special recall sorting in the current implementation.

- [ ] **Step 4: Add architecture and flow diagrams**

Add at least two ASCII diagrams: (a) a memory write/recall flow (`MemoryRecord -> MemoryWritePolicy.validate() -> MemoryEngine.write()` and `MemoryRecallPolicy -> MemoryEngine.recall()`) that shows the recall sort key `(pinned_rank, -score, index)`, and (b) a skill load/read flow (`SkillRuntime.load(path) -> SkillPackage(entrypoint + references/scripts/assets manifest) -> explicit read_reference()`).

- [ ] **Step 5: Build the fuller memory example**

Keep the existing SEMANTIC/PINNED recall example as the L1-level base case, then extend it to demonstrate what v1 never showed: a `WORKING` draft-kind memory that should not resurface next session, `MemoryRecallPolicy(allowed_kinds=...)` filtering it out, the deterministic `(pinned_rank, -score, index)` ordering, and `MemoryEngine.list_records()` as the "inspect the whole notebook" step.

- [ ] **Step 6: Build the fuller skill example**

Extend the existing `deep-research` skill folder example to include a `scripts/` and an `assets/` entry (not only `references/`), and show `package.scripts` / `package.assets` alongside `package.references`, so learners see the full skill-package shape.

- [ ] **Step 7: Break and fix, both memory and skills**

Cover at least: forbidden-phrase rejection, `max_content_chars` rejection, and one `kind not allowed` rejection for memory; path-traversal rejection and missing-reference-file rejection for skills. Frame each as Break -> diagnose from the error message -> Fix, consistent with Part 1/Part 2's Break/Fix framing. Include one explicit note that `MemoryWritePolicy.validate()` short-circuits in this order: `kind` -> `importance` -> `forbidden_phrases` -> `max_content_chars`.

- [ ] **Step 8: Add product connection and eval gate**

Explain how the Workbench memory panel, write-policy inspector, skills panel, and context inspector (Part 5) depend on memory and skill state staying inspectable now. List the exact pytest/ruff commands from the existing Eval Gate section (`tests/research_core/test_memory_engine.py`, `test_skill_runtime.py`, `test_memory_skill_evals.py`).

- [ ] **Step 9: Add reflection questions**

Include at least one tradeoff question, for example: why does `MemoryRecallPolicy` default `allowed_kinds` to every kind while `MemoryWritePolicy` should usually be configured narrower — are write and recall policies protecting against the same risk?

## Task 4: Rewrite Lab 03

**Files:**

- Modify: `course/labs/03-memory-skill-runtime-lab.md`
- Modify: `docs/progress/phases/phase-r3.md`

- [ ] **Step 1: Convert lab to L1/L2/L3**

L1 Follow: write and recall a minimal memory set, then load a skill and explicitly read one reference (follows the existing Exercise 1 and Exercise 3/4 shape). L2 Modify: predict-then-verify changes such as adding a `WORKING` memory and filtering it out via `allowed_kinds`, or tightening `max_content_chars` and watching a previously-valid record get rejected. L3 Design: no skeleton; the learner designs a new `MemoryWritePolicy`/`MemoryRecallPolicy` pair for a stated requirement (for example: pinned rules must always outrank session drafts, and drafts must never be recalled after the session ends) and a new skill folder (for example `citation-style`) with at least one reference and one script, then explicitly reads one reference. State that L3 has multiple valid designs, but every valid answer must satisfy the named invariants.

- [ ] **Step 2: Add feedback loops**

Every exercise must include Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct, matching the Lab 01/02 shape exactly.

- [ ] **Step 3: Add break/fix checks**

Include forbidden-phrase, `max_content_chars`, and `kind not allowed` scenarios for memory; path-traversal and missing-reference-file scenarios for skills, each with expected error text and a diagnosis question before the fix. Add a short Failure Output Interpretation note explaining that a multi-violation record reports the earliest failing write-policy boundary.

## Task 5: Rewrite Solution 03

**Files:**

- Modify: `course/solutions/03-memory-skill-runtime-solution.md`
- Modify: `docs/progress/phases/phase-r3.md`

- [ ] **Step 1: Provide runnable answers**

Include complete L1/L2/L3 solution snippets and assertions, covering every case introduced in Lab 03. For L3, present one reference design plus required invariants instead of implying a single canonical answer. Include assertions for pinned-first ordering, allowed-kind filtering, and no draft recall after the session boundary.

- [ ] **Step 2: Explain why answers are correct**

For each exercise, add a "What This Proves" and a "Why This Design" section, matching the Solution 01/02 shape. In the failure solutions, call out why the first error message follows the `validate()` short-circuit order.

- [ ] **Step 3: Connect design decisions forward**

Explain why memory write/recall boundaries matter for Part 4 child-context isolation (a delegated child agent should not inherit unfiltered parent memory), why skill progressive disclosure matters for Part 5's context inspector panel, and why both matter for Part 7 production diagnostics (auditing what a run actually had access to).

## Task 6: Sync Course Indexes And Progress

**Files:**

- Modify: `course/README.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r3.md`

- [ ] **Step 1: Mark Part 3 as R3 rewritten**

After Tasks 3-5 land, update course indexes to describe Part 3 as completed R3 material. Keep Parts 4-7 as current v1 material.

- [ ] **Step 2: Verify docs freshness**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: passes with all indexed paths resolved.

## Task 7: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r3.md`

- [ ] **Step 1: Run final verification**

Run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [ ] **Step 2: Run the markdown Python block gate**

Run the pytest-backed markdown Python block gate for Chapter 03, Lab 03, and Solution 03. Manually inspect only snippets that are intentionally outside the selected executable file list. This replaces the R1/R2 copy/paste-only discipline with an automated check for changed Part 3 examples.

- [ ] **Step 3: Clean generated artifacts**

Remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.

- [ ] **Step 4: Run final docs reconciliation**

Use the neat-freak workflow to verify docs/progress/README/AGENTS alignment.

- [ ] **Step 5: Mark R3 complete**

Only after fresh verification, mark R3 complete and commit the final docs sync.

## Exit Criteria

- Part 3 Chapter/Lab/Solution are rewritten around the "assistant has no notebook" problem, with both the memory-notebook and skills-backpack mental models present.
- Chapter 03 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- Lab 03 includes L1 Follow, L2 Modify, and L3 Design exercises with full Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback for each.
- The rewrite exercises `max_content_chars`, `MemoryRecallPolicy.allowed_kinds`, `MemoryEngine.list_records()`, and skill `scripts`/`assets` discovery, none of which the v1 material covered.
- Chapter 03 teaches one "when to use" sentence for all six `MemoryKind` values and explicitly shows that recall sorting uses `(pinned_rank, -score, index)`.
- Lab/Solution 03 teach the `validate()` short-circuit order and use a reference-design-plus-invariants pattern for the open-ended L3 exercise.
- Solution 03 explains what each assertion proves and why the design matters for Part 4, Part 5, and Part 7.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R3 status while Parts 4-7 remain marked as current v1 material.
- No runtime/product code changes were needed; only the markdown Python block infra/test gate was added.
- Changed Part 3 fenced Python blocks are executed against the real `research_core.memory` / `research_core.skills` API by `tests/course/test_markdown_python_blocks.py`.
- Final verification is recorded in `docs/progress/phases/phase-r3.md` and `docs/progress/overall.md`.

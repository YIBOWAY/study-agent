# Phase R4: Part 4 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Part 4 so Multi-Agent Delegation teaches child-context isolation and budget accounting through the local paper research assistant's "hand a sub-task to a focused helper without leaking parent context, blowing the budget, or hiding failures" problem, using the project-driven teaching contract established in Phase R1 and continued in Phases R2 and R3.

**Architecture:** No runtime/product code changes. R4 only rewrites `course/chapters/04-multi-agent-delegation.md`, `course/labs/04-delegation-runtime-lab.md`, `course/solutions/04-delegation-runtime-solution.md`, extends the markdown Python block gate to cover Part 4 (and backfills Part 1/Part 2 into the gate), and updates the docs/progress surfaces that index them. The rewrite uses existing `research_core.delegation` contracts: `AgentRolePolicy`, `DelegationTask`, `DelegationBudget`, `DelegationRuntime`, `DelegationResult`, `DelegationMergeResult`, `DelegationStatus`, `compile_child_prompt`, and `A2AAdapterStub`.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`.

---

## First-Principles Review

R3 completed the Part 3 teaching rewrite and, as a hardening step, added an automated markdown Python block gate (`infra/markdown_python_blocks.py` + `tests/course/test_markdown_python_blocks.py`) that executes fenced Python blocks and compares marked `Expected output:` fences. That gate currently only covers the three Part 3 files. The current Part 4 files (`chapters/04-multi-agent-delegation.md`, `labs/04-delegation-runtime-lab.md`, `solutions/04-delegation-runtime-solution.md`) are still v1 material. Reading them against the Part Contract in `docs/course/roadmap.md` shows concrete gaps, not just a style mismatch:

- No Problem Hook narrative. The chapter opens with a "Goal" section and a Core Objects table, not a concrete failure the researcher experiences when delegating.
- No mental-model analogy. There is no "delegation = 把一小块活外包给专注的下属" story mapping `AgentRolePolicy` / `DelegationTask` / `DelegationBudget` / parent events / `DelegationMergeResult` to plain-language roles, the way Part 2 used a detective story and Part 3 used a notebook and a skill backpack.
- Only `DelegationRuntime.run_task` (single child) is demonstrated. `run_many`, `max_total_steps` sequential accounting, and duplicate `task id` / `child_run_id` rejection are never shown, even though "budget accounting" is the headline promise for this Part in the roadmap.
- `DelegationMergeResult` is listed in the Core Objects table but never built. The auto-derivation of `unresolved_conflicts` from non-`COMPLETED` results (and `DelegationMergeResult.from_results`) is never exercised, so learners never see how a parent keeps unresolved child outcomes visible instead of silently dropping them.
- Context isolation is named as the point (`metadata={"private_parent_history": "This must not leak."}`) but the mechanism is never inspected. The chapter does not show that only `context_messages` reach `compile_child_prompt`, that parent `metadata` is not sent to the child, and that a `SYSTEM` message in `context_messages` is rejected outright.
- `DelegationResult.step_count` (which counts child `MODEL_REQUEST` events) is the quantity every budget check uses, but the chapter never explains how a "step" is counted, so the budget errors look arbitrary.
- The parent event trail (`DELEGATE_START` -> `DELEGATE_EVENT*` -> `DELEGATE_FINISH`) is produced but never taught as the audit surface, even though inspecting the event trail is the habit Part 1 and Part 2 established.
- Failure paths (child raises, observed step budget exceeded, role budget too large, duplicate ids, system-message leak) are not framed as a tiered Break -> diagnose -> Fix cycle with diagnosis questions.
- Lab 04 has flat "Exercise" blocks with no L1/L2/L3 tiering and no Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback loop.
- There are no ASCII diagrams anywhere in the current Part 4 material and no `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.

I verified the parts of the real `research_core.delegation` API that the current v1 material does not exercise, so the rewrite has accurate new material to draw on (all outputs below were confirmed by running the exact snippets from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`):

```python
# 1. Context isolation is a hard boundary: a SYSTEM message in context is rejected.
DelegationTask(
    id="t", parent_run_id="p", child_run_id="c", objective="o", role=role,
    context_messages=[AgentMessage(id="s", role=MessageRole.SYSTEM, content="x")],
)
# -> ValueError: context_messages must not include system messages

# 2. A successful run_task emits an inspectable parent event trail and a step_count.
result.status.value           # -> 'completed'
result.step_count             # -> 1   (counts child MODEL_REQUEST events)
[e.type.value for e in result.parent_events]
# -> ['delegate_start', 'delegate_event', 'delegate_event', 'delegate_finish']

# 3. Observed step budget overflow -> FAILED, not an exception.
res2.status.value             # -> 'failed'
res2.error_message
# -> 'child step count 5 exceeds allowed max steps 2 (role max_steps 2, max_steps_per_child 2)'

# 4. A role that wants more steps than the budget allows is rejected before running.
runtime.run_task(task_big, budget=DelegationBudget(max_steps_per_child=2, ...))
# -> ValueError: task tb role max_steps 9 exceeds max_steps_per_child 2

# 5. run_many rejects duplicate child_run_id (and duplicate task id) up front.
runtime.run_many([task_a, task_b_with_same_child_run_id], budget=...)
# -> ValueError: duplicate child_run_id: dup

# 6. DelegationMergeResult auto-derives unresolved_conflicts from non-completed results.
merge = DelegationMergeResult.from_results([completed_result, failed_result], summary="merged")
len(merge.unresolved_conflicts)                              # -> 1
[d.status.value for d in merge.unresolved_conflicts]         # -> ['failed']
```

Therefore R4 should not add new code to `packages/` or `apps/`. The existing Delegation implementation already has enough surface area for a full Part Contract rewrite; the current material simply teaches a single-child slice of it. The phase succeeds when Part 4 follows the same rhythm as Parts 1-3:

- problem hook: "把一小块研究任务外包给下属，结果下属看到了父上下文里不该看的东西，或者跑超了预算，或者失败了却在最终汇总里被悄悄吞掉";
- mental model: delegation = 把一小块活外包给一个专注的下属。工牌（`AgentRolePolicy`）决定他是谁、能用什么；任务单（`DelegationTask`）只给他该看的资料；预算（`DelegationBudget`）限制他能花多少步；回执（parent `delegate_*` events）记录他做了什么；未结清清单（`DelegationMergeResult.unresolved_conflicts`）保证失败不会被藏起来;
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop covering both a single delegation and a multi-task budget;
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops, including an L3 that asks the learner to design a role + budget + merge policy for a stated requirement (for example: two child reviewers, a hard total-step ceiling, and a rule that any non-completed child must remain visible as an unresolved conflict);
- at least two ASCII diagrams: a delegation flow (`DelegationTask -> DelegationRuntime.run_task -> DELEGATE_START / DELEGATE_EVENT* / DELEGATE_FINISH -> DelegationResult`) and a budget/step-accounting diagram showing how `step_count` (child `MODEL_REQUEST` count) is checked against `role.max_steps`, `max_steps_per_child`, and `max_total_steps`;
- a context-isolation section that inspects `compile_child_prompt(task)` to prove only `context_messages` reach the child, tying back to the Part 3 memory boundary ("a delegated child must not inherit unfiltered parent memory");
- a Workbench connection section explaining why the delegation timeline and unresolved conflicts must stay inspectable for the product panels planned in Part 5;
- offline verification only.

## Global Constraints

- Do not modify `packages/research_core`, `apps/api`, `apps/web`, or product/runtime tests in this phase.
- Do not introduce real concurrency, remote workers, network calls, API keys, or a real A2A transport. Keep `A2AAdapterStub` as a deterministic export boundary only.
- Use only the existing `research_core.delegation` contracts; do not add new fields or methods to them.
- Keep all snippets runnable from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`.
- Keep Parts 5-7 labeled as current v1 material until their own R5-R7 rewrites land.
- Update `docs/progress/` after each landed task or milestone.
- Commit and push each milestone with a detailed commit message.

## File Map

Create:

- `docs/plans/2026-07-01-phase-r4-course-teaching-redesign.md`
- `docs/progress/phases/phase-r4.md`

Modify:

- `infra/markdown_python_blocks.py` (only if the gate needs a helper for Part 4 patterns; prefer no change)
- `tests/course/test_markdown_python_blocks.py` (add Part 4 files; backfill Part 1/Part 2 files)
- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `course/README.md`
- `course/chapters/04-multi-agent-delegation.md`
- `course/labs/04-delegation-runtime-lab.md`
- `course/solutions/04-delegation-runtime-solution.md`
- `AGENTS.md` and `infra/local-readiness-checklist.md` (only if the gate scope note needs updating)

## Task 1: Start R4 Plan And Progress

**Files:**

- Create: `docs/plans/2026-07-01-phase-r4-course-teaching-redesign.md`
- Create: `docs/progress/phases/phase-r4.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/README.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this plan**

Save this plan under `docs/plans/` (already done by this task's authoring step).

- [x] **Step 2: Start progress tracking**

Create `docs/progress/phases/phase-r4.md` with R4 scope, task checklist, verification target, and a start log dated with the actual start date.

- [x] **Step 3: Update indexes**

Update `docs/README.md`, `docs/progress/README.md`, `docs/progress/overall.md`, and `docs/plans/2026-06-25-redesign-execution-roadmap.md` so R4 is visible as active, without marking rewritten course content complete yet.

- [x] **Step 4: Verify indexed docs paths**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: docs freshness passes.

- [x] **Step 5: Commit**

Commit the plan/progress kickoff on a phase branch (for example `codex/redesign-course-r4`).

## Task 2: Extend The Markdown Python Block Gate To Part 4

**Files:**

- Modify: `tests/course/test_markdown_python_blocks.py`
- Modify: `infra/markdown_python_blocks.py` (only if needed)
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Add Part 4 files to the gate (TDD)**

Add the three Part 4 files to the checked set. Because Part 4 has not been rewritten yet, first confirm the gate meaningfully executes them; if the v1 blocks are not self-contained, that is acceptable until Task 3-5 replace them. The intent is that by the end of R4, `tests/course/test_markdown_python_blocks.py` covers Part 4 the same way it covers Part 3.

- [x] **Step 2: Backfill Part 1 and Part 2 into the gate**

Add the Part 1 and Part 2 chapter/lab/solution files to the gate so the already-verified R1/R2 code blocks are locked against future API drift, closing the "only Part 3 is automated" gap. If any R1/R2 block is not executable in a shared namespace (for example, it intentionally shows a bare error), adjust the block minimally in its own R-phase spirit or document why it is excluded; do not silently weaken the gate.

- [x] **Step 3: Verify the gate**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
```

Expected: passes for all included files.

## Task 3: Rewrite Chapter 04

**Files:**

- Modify: `course/chapters/04-multi-agent-delegation.md`
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Rewrite opener and learner contract**

Turn Chapter 04 into "Part 4: Multi-Agent Delegation" with a Learner Contract block (Who this is for / Before you start / You will build / You will be able to explain / You will prove it works by running / Offline guarantee), matching the Chapter 02/03 shape, and update the project progress tracker so Part 3 is `[x]` and Part 4 is `[*]`.

- [x] **Step 2: Open with the problem hook**

Start from the researcher delegating a sub-task (for example "让一个 reviewer child 只核对这批证据"). Show the three failures that motivate the Part: the child sees parent-only context it should not, the child runs more steps than the budget allows, and a failed child is silently dropped from the final summary. Name these before introducing any object.

- [x] **Step 3: Introduce the mental model**

Delegation = 把一小块活外包给一个专注的下属。Use a story-role table like Chapter 02/03 mapping `AgentRolePolicy` (工牌/角色边界), `DelegationTask` (任务单，只给该看的资料), `DelegationBudget` (预算), parent `delegate_*` events (回执/轨迹), `DelegationResult` (单个下属的结果), and `DelegationMergeResult` (汇总 + 未结清清单).

- [x] **Step 4: Add architecture and flow diagrams**

Add at least two ASCII diagrams: (a) a delegation flow (`DelegationTask -> DelegationRuntime.run_task -> DELEGATE_START / DELEGATE_EVENT* / DELEGATE_FINISH -> DelegationResult`), and (b) a budget/step-accounting diagram showing how `step_count` (child `MODEL_REQUEST` count) is compared against `role.max_steps`, `max_steps_per_child`, and `max_total_steps`.

- [x] **Step 5: Build the single-delegation example and inspect it**

Keep a deterministic `FixedChildRunner` as the base case. Show `run_task` returning a `COMPLETED` result, then Inspect: print `result.status`, `result.step_count`, and `[e.type.value for e in result.parent_events]` so learners see the `delegate_start / delegate_event / delegate_finish` trail. Add a context-isolation Inspect step that prints `compile_child_prompt(task)` to prove parent `metadata` never reaches the child, tying back to the Part 3 memory boundary.

- [x] **Step 6: Build the multi-task budget example**

Extend to `run_many` with two tasks and a `max_total_steps` ceiling. Show sequential step accounting consuming the total budget, and build a `DelegationMergeResult` (via `from_results`) so learners see `unresolved_conflicts` auto-derived from any non-`COMPLETED` result.

- [x] **Step 7: Break and fix**

Cover at least: a `SYSTEM` message in `context_messages` (`context_messages must not include system messages`), an observed step-budget overflow that returns a `FAILED` result with `child step count N exceeds allowed max steps M`, a role budget that is too large (`role max_steps ... exceeds max_steps_per_child ...`), and a `run_many` duplicate `child_run_id` (`duplicate child_run_id: ...`). Frame each as Break -> diagnose from the message -> Fix, consistent with Part 1-3 framing, and note which failures raise up front versus which are recorded as a `FAILED` result.

- [x] **Step 8: Add product connection and eval gate**

Explain how the Workbench delegation timeline panel and unresolved-conflicts view (Part 5) depend on the parent event trail and merge result staying inspectable now. List the exact pytest/ruff commands for the existing delegation tests plus `tests/course/test_markdown_python_blocks.py`.

- [x] **Step 9: Add reflection questions**

Include at least one tradeoff question, for example: why does an over-budget child produce a `FAILED` result instead of raising, while a role that is misconfigured too large raises before running — what is the difference between a policy error and an observed-runtime overflow?

## Task 4: Rewrite Lab 04

**Files:**

- Modify: `course/labs/04-delegation-runtime-lab.md`
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Convert lab to L1/L2/L3**

L1 Follow: run a single delegation with a deterministic child runner, then inspect `status`, `step_count`, and the parent event trail. L2 Modify: predict-then-verify changes such as tightening `max_steps_per_child` until a previously-passing child produces a `FAILED` result, and running `run_many` until `max_total_steps` is exhausted. L3 Design: no skeleton; the learner designs a role + budget + merge policy for a stated requirement (for example two reviewer children, a hard total-step ceiling, and a rule that any non-completed child must remain in `unresolved_conflicts`), then proves the required invariants.

- [x] **Step 2: Add feedback loops**

Every exercise must include Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct, matching the Lab 02/03 shape exactly.

- [x] **Step 3: Add break/fix checks**

Include system-message rejection, observed step-budget overflow, role-too-large rejection, and duplicate-id rejection, each with expected error text and a diagnosis question before the fix.

## Task 5: Rewrite Solution 04

**Files:**

- Modify: `course/solutions/04-delegation-runtime-solution.md`
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Provide runnable answers**

Include complete L1/L2/L3 solution snippets and assertions, covering every case introduced in Lab 04. Use `assert`-based self-verification for solution blocks (as Solution 03 does) so the markdown gate executes and checks them.

- [x] **Step 2: Explain why answers are correct**

For each exercise, add a "What This Proves" and a "Why This Design" section, matching the Solution 02/03 shape. For the open-ended L3, provide one reference design plus the required invariants rather than a single canonical answer.

- [x] **Step 3: Connect design decisions forward**

Explain why context isolation matters for Part 5's context inspector (the product must show what a child actually received), why the parent event trail matters for Part 7 production diagnostics (auditing what a delegated run did), and why keeping unresolved conflicts visible matters for trustworthy multi-agent output. Tie the context-isolation boundary back to Part 3's memory recall boundary.

## Task 6: Sync Course Indexes And Progress

**Files:**

- Modify: `course/README.md`
- Modify: `docs/README.md`
- Modify: `docs/course/roadmap.md`
- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Mark Part 4 as R4 rewritten**

After Tasks 2-5 land, update course indexes to describe Part 4 as completed R4 material. Keep Parts 5-7 as current v1 material.

- [x] **Step 2: Verify docs freshness**

Run:

```bash
cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
```

Expected: passes with all indexed paths resolved.

## Task 7: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`
- Modify: `docs/progress/phases/phase-r4.md`

- [x] **Step 1: Run final verification**

Run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [x] **Step 2: Manually re-run every new/changed course code block**

Even with the markdown gate, paste every changed code block in Chapter 04, Lab 04, and Solution 04 into a real `PYTHONPATH=packages/research_core/src uv run python` shell and confirm the output matches the documented output exactly, the same way R1-R3 were verified. The gate compares stdout only for blocks with an adjacent `Expected output:` fence; blocks without one are execution-only, so a manual pass still catches output text that the gate does not compare.

- [x] **Step 3: Clean generated artifacts**

Remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.

- [x] **Step 4: Run final docs reconciliation**

Use the neat-freak workflow to verify docs/progress/README/AGENTS alignment, including the markdown-gate scope note now that it covers Parts 1-4.

- [x] **Step 5: Mark R4 complete**

Only after fresh verification, mark R4 complete and commit the final docs sync.

## Exit Criteria

- Part 4 Chapter/Lab/Solution are rewritten around the "delegate without leaking context, overspending budget, or hiding failures" problem, with the delegation mental model present.
- Chapter 04 has at least two ASCII diagrams (delegation flow and budget/step accounting) and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- Lab 04 includes L1 Follow, L2 Modify, and L3 Design exercises with full Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback for each.
- The rewrite exercises `run_many`, `max_total_steps` accounting, duplicate `task id` / `child_run_id` rejection, `DelegationMergeResult` unresolved-conflict derivation, context isolation via `compile_child_prompt`, and the parent `delegate_*` event trail, none of which the v1 material covered.
- Solution 04 explains what each assertion proves and why the design matters for Part 5 and Part 7, and ties context isolation back to Part 3 memory boundaries.
- The markdown Python block gate covers Part 4, and Part 1/Part 2 are backfilled into the gate so R1-R4 code blocks are all locked against drift.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R4 status while Parts 5-7 remain marked as current v1 material.
- No runtime/product code changes were needed.
- Every changed code block was manually re-run against the real `research_core.delegation` API and matched documented output exactly.
- Final verification is recorded in `docs/progress/phases/phase-r4.md` and `docs/progress/overall.md`.

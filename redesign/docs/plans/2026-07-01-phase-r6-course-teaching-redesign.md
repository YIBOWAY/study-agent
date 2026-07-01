# Phase R6: Part 6 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Part 6 so Framework Comparisons teaches how to make a defensible framework/build decision — pin the same task, fixture, and metric, then let a weighted score decide — through the local paper research assistant's "someone asks why you did not just use LangChain/CrewAI" problem, using the project-driven teaching contract established in Phases R1-R5.

**Architecture:** No runtime/product code changes and no infra/gate code change. R6 rewrites `course/chapters/06-framework-comparisons.md`, `course/labs/06-framework-comparisons-lab.md`, `course/solutions/06-framework-comparisons-solution.md`; adds the three Part 6 files to the markdown Python block gate's `COURSE_MARKDOWN_PATHS`; and updates the docs/progress surfaces that index them. The rewrite uses the existing `course.framework_comparisons` contracts in `course/framework_comparisons/common.py`: `ComparisonTask`, `TaskRunSummary`, `FrameworkProfile`, `FrameworkRecommendation`, `build_echo_tool_task`, `build_state_resume_task`, `run_handwritten_task`, `default_framework_profiles`, `build_recommendation_matrix`, `recommend_profile`, and the `SCORE_CRITERIA` tuple.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=.:packages/research_core/src uv run python` (the leading `.` puts the redesign root on the path so `course.framework_comparisons` imports).

---

## First-Principles Review

R5 completed the Part 5 Workbench Product rewrite and extended the markdown gate to run `apps/api/src` blocks. The current Part 6 files (`chapters/06-framework-comparisons.md`, `labs/06-framework-comparisons-lab.md`, `solutions/06-framework-comparisons-solution.md`) are still v1 material. Reading them against the Part Contract in `docs/course/roadmap.md` shows concrete gaps, not just a style mismatch:

- No Learner Contract block and no Problem Hook narrative. The chapter opens with a "Goal" section, not the concrete moment where a teammate/manager asks "why did you hand-write this instead of using LangChain / CrewAI / PydanticAI?" and the decision has to be defended with evidence rather than vibes.
- No mental-model analogy. There is no "this is a build-vs-adopt technical-selection decision, and the recommendation matrix is your decision record" story mapping `ComparisonTask` / `FrameworkProfile` / weights / `FrameworkRecommendation` to plain-language roles, the way Part 2 used a detective story, Part 3 a notebook/backpack, Part 4 a delegated helper, and Part 5 a dashboard.
- The scoring mechanism is invisible. The v1 chapter prints "echo_tool_trace -> handwritten, score 0.854" and "state_resume_workflow -> langgraph, score 0.78" but never shows HOW the score is computed. The real formula in `_score_profile_for_task` is `total = round(sum(profile.score_for(c) * weight[c] for c in weights) / sum(weight.values()), 4)`; `strengths` are the weighted criteria where the profile scores `>= 0.8`; `tradeoffs` are the weighted criteria where it scores `< 0.55`. None of this transparency is taught, so the winning number looks like an oracle instead of a defensible calculation — which defeats the entire point of the Part.
- The seven `SCORE_CRITERIA` (`inspectability`, `offline_testing`, `typed_contracts`, `state_resume`, `multi_agent`, `product_boundary`, `team_cost`) and the six `default_framework_profiles` (`handwritten`, `pydantic-ai`, `llamaindex-workflows`, `langgraph`, `openai-agents-sdk`, `crewai`) are dumped as a table but never connected to WHY a given task's weights make a given profile win or lose.
- `recommend_profile`'s deterministic tie-break (`sorted(matches, key=lambda i: (-i.total_score, i.profile_id))[0]`) is never taught, so learners cannot explain why ties resolve the way they do.
- The core lesson — "same task fixture, different weights => different winner" — is stated once in the v1 lab (`state_heavy_echo`) but never turned into a predict-then-verify exercise or an L3 design exercise.
- Lab 06 has flat "Exercise 1-4" blocks with no L1/L2/L3 tiering and no Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback loop.
- There are no ASCII diagrams and no `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts anywhere in the current Part 6 material.
- The v1 chapter's "Failure Lab Preview" block and the v1 Lab's Exercise 4 raise `ValueError` UNCAUGHT. Verified: running the markdown gate on the v1 chapter fails at that block (`06-framework-comparisons.md:155: python block failed: ValueError: unknown weight criteria: marketing_claims`). The rewrite must wrap every error-demonstrating block in `try/except` so the shared-namespace gate does not abort, exactly as Parts 1-5 do.

I verified the real `course.framework_comparisons` behavior the rewrite will teach (all confirmed by running snippets from `redesign/` with `PYTHONPATH=.:packages/research_core/src`, and by running the markdown gate module against the v1 chapter):

```python
# 1. The handwritten baseline really runs AgentRunner + FakeModel + ToolRuntime.
run_handwritten_task(build_echo_tool_task()).to_record()
# -> event_sequence: model_request, model_response, tool_call, tool_result, model_request, model_response
#    tool_call_count: 1 ; error_count: 0 ; final_answer: "The echo tool returned hello."

# 2. Recommendations are task-relative; the same profile set yields different winners.
recommend_profile(matrix, task_id="echo_tool_trace").profile_id       # -> "handwritten" (score 0.854)
recommend_profile(matrix, task_id="state_resume_workflow").profile_id # -> "langgraph" (score 0.78)

# 3. The score is a transparent weighted average, not an oracle:
#    total = round(sum(profile.score_for(c) * w[c] for c in weights) / sum(weights.values()), 4)
#    strengths = weighted criteria with profile score >= 0.8 ; tradeoffs = weighted criteria with score < 0.55

# 4. The metric surface is controlled; bad criteria are rejected at construction:
ComparisonTask(..., weights={"marketing_claims": 1.0})   # -> ValueError: unknown weight criteria: marketing_claims
ComparisonTask(..., weights={})                          # -> ValueError: weights must not be empty
ComparisonTask(..., weights={"inspectability": 0.0})     # -> ValueError: inspectability weight must be positive
FrameworkProfile(...).score_for("bogus")                 # -> ValueError: unknown score criterion 'bogus'
recommend_profile(matrix, task_id="missing")             # -> ValueError: no recommendations found for task 'missing'
```

I also verified the gate constraint that shapes the gate task below. Unlike R5 (where `apps/api/src` genuinely was not importable and the gate helper had to change), Part 6's `course.framework_comparisons` import already works under the gate with NO helper change: the redesign root is on `sys.path` via the `python -m` current-directory behaviour when run from `redesign/`, and via the pytest `pythonpath = [".", ...]` entry in `pyproject.toml` when the gate runs as a test. The v1-chapter gate run above imported `course.framework_comparisons` successfully and only failed on the uncaught `ValueError` block, proving the import path is fine. Therefore R6 needs NO infra/gate code change; the only gate work is adding the three Part 6 files to `COURSE_MARKDOWN_PATHS` once they are rewritten to be gate-clean (every error block self-caught).

Therefore R6 should not change `course/framework_comparisons/common.py`, `infra/`, `packages/`, or `apps/`. The existing comparison harness already has enough depth (transparent weighted scoring, strengths/tradeoffs derivation, deterministic tie-break, controlled metric surface) for a full Part Contract rewrite; the current material simply presents the winning numbers without the reasoning. The phase succeeds when Part 6 follows the same rhythm as Parts 1-5:

- problem hook: "有人问你'为什么不直接用 LangChain / CrewAI'——你不能靠感觉回答，要靠一个固定 task、固定 fixture、固定 metric 的可复现比较";
- mental model: framework comparison = 一次 build-vs-adopt 技术选型。`ComparisonTask` = 统一考卷（同一任务、同一 fixture、同一权重），`FrameworkProfile` = 每个候选在各维度的评分卡（课程记录，不是第三方 wrapper），weights = 这次决策更看重什么，`FrameworkRecommendation` = 可追溯的决策记录（含 total_score、strengths、tradeoffs），`run_handwritten_task` = 用真实 `AgentRunner` 跑出的手写基线;
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop: Build runs the handwritten baseline and the recommendation matrix; Inspect opens up the weighted-score computation and the strengths/tradeoffs derivation for one profile on one task so the number is explainable; Break/Fix triggers the controlled-metric failures;
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops, including an L2 that changes a task's weights and predicts how the winner shifts (with the learner explaining WHY via the weighted formula) and an L3 that designs a NEW `ComparisonTask` (its own scenario + weights) for a stated requirement, predicts the winner, and verifies it — achievable with existing contracts and no new code;
- at least two ASCII diagrams: (a) the comparison harness flow (`ComparisonTask (+weights) x FrameworkProfile -> _score_profile_for_task -> FrameworkRecommendation -> recommend_profile winner`), and (b) a weighted-score computation diagram showing `sum(profile.score * weight) / sum(weights)` plus the `>=0.8` strengths / `<0.55` tradeoffs cutoffs;
- a product-boundary section reinforcing that all comparison code stays under `course/framework_comparisons/` and never enters `research_core` / `apps`, tying back to the offline-first, handwritten-baseline direction;
- offline verification only (no third-party frameworks installed; profiles are deterministic course records).

## Global Constraints

- Do not modify `course/framework_comparisons/common.py`, `packages/research_core/`, `apps/`, or `infra/`. Teaching-only changes plus adding Part 6 files to the gate's checked list.
- Do NOT install or import any third-party agent framework (PydanticAI, LangGraph, LlamaIndex, OpenAI Agents SDK, CrewAI). `FrameworkProfile` stays a deterministic course record.
- Do not introduce network calls, API keys, real providers, or a real framework adapter.
- Use only the existing `course.framework_comparisons` contracts; invent no new criteria, profiles, fields, or functions.
- Keep all Python snippets runnable from `redesign/` with `PYTHONPATH=.:packages/research_core/src`. State this path at the top of each snippet group.
- Every error-demonstrating Python block must self-catch (`try/except`) so the shared-namespace markdown gate does not abort.
- Keep Part 7 labeled as current v1 material until its own R7 rewrite lands.
- Update `docs/progress/` after each landed task or milestone.
- Commit each milestone with a detailed commit message. Push only when the user approves pushing.

## File Map

Create:

- `docs/progress/phases/phase-r6.md`

Modify:

- `tests/course/test_markdown_python_blocks.py` (add the three Part 6 files to `COURSE_MARKDOWN_PATHS`)
- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `course/README.md`
- `README.md`
- `course/chapters/06-framework-comparisons.md`
- `course/labs/06-framework-comparisons-lab.md`
- `course/solutions/06-framework-comparisons-solution.md`

## Task 1: Start R6 Plan And Progress

**Files:**

- Create: `docs/progress/phases/phase-r6.md`
- Modify: `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/README.md`, `docs/progress/overall.md`, `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Add this plan** — save this plan under `docs/plans/` (already done by this authoring step).
- [ ] **Step 2: Start progress tracking** — create `docs/progress/phases/phase-r6.md` with R6 scope, task checklist, verification target, and a start log dated with the actual start date.
- [ ] **Step 3: Update indexes** — update the docs/progress indexes and the execution roadmap so R6 is visible as active, without marking rewritten course content complete yet. Add the R6 plan link to `docs/README.md` and `docs/course/roadmap.md`.
- [ ] **Step 4: Verify indexed docs paths** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: docs freshness passes.
- [ ] **Step 5: Commit** — commit the plan/progress kickoff on a phase branch (for example `codex/redesign-course-r6`).

## Task 2: Rewrite Chapter 06

**Files:**

- Modify: `course/chapters/06-framework-comparisons.md`
- Modify: `docs/progress/phases/phase-r6.md`

- [ ] **Step 1: Rewrite opener and learner contract** — turn Chapter 06 into "Part 6: Framework Comparisons" with a Learner Contract block (Who this is for / Before you start / You will build / You will be able to explain / You will prove it works by running / Offline guarantee), matching Chapter 02-05, and update the project progress tracker so Part 5 is `[x]` and Part 6 is `[*]`.
- [ ] **Step 2: Open with the problem hook** — start from a teammate/manager asking "why not just use LangChain/CrewAI?"; name the failure to avoid (each framework runs its own favourite demo = a brochure, not a comparison) and the fix (pin the same task, fixture, and metric, then let a weighted score decide).
- [ ] **Step 3: Introduce the mental model** — framework comparison = a build-vs-adopt technical-selection decision. Use a story-role table mapping `ComparisonTask` (统一考卷/固定 task+fixture+weights), `FrameworkProfile` (评分卡/课程记录), weights (这次决策看重什么), `FrameworkRecommendation` (可追溯决策记录), and `run_handwritten_task` (真实手写基线) to their roles.
- [ ] **Step 4: Add architecture and scoring diagrams** — add at least two ASCII diagrams: (a) the harness flow (`ComparisonTask (+weights) x FrameworkProfile -> _score_profile_for_task -> FrameworkRecommendation -> recommend_profile winner`), and (b) a weighted-score computation diagram showing `sum(profile.score * weight) / sum(weights)` with the `>=0.8` strengths and `<0.55` tradeoffs cutoffs.
- [ ] **Step 5: Build the baseline and make the score transparent** — run `run_handwritten_task(build_echo_tool_task())` and inspect its record; build the recommendation matrix; then Inspect the scoring by reproducing one profile's `total_score` for one task by hand (sum of `profile.score_for(c) * weight[c]` over the task weights, divided by the weight total) and by printing the winner's `strengths` / `tradeoffs`, so the winning number is explainable rather than magic. Use `FrameworkProfile.score_for(...)` and the task `weights`.
- [ ] **Step 6: Teach the task-relative winner** — show the echo task -> handwritten and the state/resume task -> langgraph, and explain via the weights why each wins. Mention the deterministic tie-break in `recommend_profile` (`-total_score`, then `profile_id`).
- [ ] **Step 7: Break and fix the controlled metric surface** — trigger and diagnose, each self-caught: `unknown weight criteria: marketing_claims`, `weights must not be empty`, a non-positive weight (`... weight must be positive`), `unknown score criterion 'bogus'` from `FrameworkProfile.score_for`, and `no recommendations found for task '...'` from `recommend_profile`. Frame each as Break -> diagnose from the message -> Fix, and explain why an uncontrolled metric makes a comparison drift.
- [ ] **Step 8: Add product boundary and eval gate** — reinforce that comparison code stays under `course/framework_comparisons/` and never enters `research_core`/`apps`; connect forward to Part 7 (a real framework adoption would need its own approved phase, tests, and docs). List the exact pytest/ruff commands for `tests/course/test_framework_comparisons.py` plus `tests/course/test_markdown_python_blocks.py`.
- [ ] **Step 9: Add reflection questions** — include at least one tradeoff question, for example: why does the course keep the handwritten runtime as the product baseline even though LangGraph wins the state/resume task — what would have to change about the real workload before adopting a framework is the right call?

## Task 3: Rewrite Lab 06

**Files:**

- Modify: `course/labs/06-framework-comparisons-lab.md`
- Modify: `docs/progress/phases/phase-r6.md`

- [ ] **Step 1: Convert lab to L1/L2/L3** — L1 Follow: run the handwritten baseline and inspect its summary; build and print the recommendation matrix. L2 Modify (predict-then-verify): copy `build_echo_tool_task()` and raise the `state_resume` weight, predict the new winner and explain via the weighted formula, then verify; also reproduce one `total_score` by hand and assert it matches `FrameworkRecommendation.total_score`. L3 Design (no skeleton): design a NEW `ComparisonTask` (own id/title/weights) for a stated scenario (for example a multi-agent-heavy review task), predict which profile should win, build the matrix, and assert the predicted winner — with the runnable reference answer living in the Solution, and the lab's open-ended self-check as a NON-EXECUTED ```text block (like Lab 04/05's L3).
- [ ] **Step 2: Add feedback loops** — every exercise includes Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct, matching Lab 02-05.
- [ ] **Step 3: Add break/fix checks** — include unknown weight criteria, empty weights, non-positive weight, unknown score criterion, and no-recommendations-for-task, each with the exact expected error text and a diagnosis question before the fix, each self-caught.

## Task 4: Rewrite Solution 06

**Files:**

- Modify: `course/solutions/06-framework-comparisons-solution.md`
- Modify: `docs/progress/phases/phase-r6.md`

- [ ] **Step 1: Provide runnable answers** — include complete L1/L2/L3 solution snippets with `assert`-based self-verification (the markdown gate runs and enforces these). L3 is the runnable reference design for the new `ComparisonTask`, stated as one valid answer among many that satisfy the same invariant (the predicted winner matches `recommend_profile`).
- [ ] **Step 2: Explain why answers are correct** — for each exercise add "What This Proves" and "Why This Design", matching Solution 02-05. Include a manual `total_score` reproduction so the assertion proves the score is a transparent weighted average, not an oracle.
- [ ] **Step 3: Connect design decisions forward** — explain why the handwritten baseline stays the product/teaching baseline, why metrics must be controlled in code for reports to stay honest, and what a real framework adoption in a later phase would require (its own approved plan, adapter location outside `research_core`, tests, and docs).

## Task 5: Add Part 6 To The Gate And Sync Indexes

**Files:**

- Modify: `tests/course/test_markdown_python_blocks.py`
- Modify: `course/README.md`, `README.md`, `docs/README.md`, `docs/course/roadmap.md`, `docs/plans/2026-06-25-redesign-execution-roadmap.md`, `docs/progress/overall.md`, `docs/progress/phases/phase-r6.md`

- [ ] **Step 1: Add Part 6 files to the gate** — append the three Part 6 chapter/lab/solution paths to `COURSE_MARKDOWN_PATHS`. No helper change is needed (verified: `course.framework_comparisons` imports under the gate). Run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q`; expected: passes with Part 6 included.
- [ ] **Step 2: Mark Part 6 as R6 rewritten** — update `course/README.md`, `README.md`, `docs/course/roadmap.md`, execution roadmap, and progress indexes to describe Part 6 as completed R6 material. Keep Part 7 as current v1 material.
- [ ] **Step 3: Verify docs freshness** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: passes with all indexed paths resolved.

## Task 6: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`, `docs/progress/phases/phase-r6.md`

- [ ] **Step 1: Run final verification** — run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [ ] **Step 2: Manually re-run every new/changed course code block** — run the gate module directly on each Part 6 file (`PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/06-framework-comparisons.md course/labs/06-framework-comparisons-lab.md course/solutions/06-framework-comparisons-solution.md --project-root .`) and confirm all blocks execute and every `Expected output:` matches, the same way R1-R5 were verified.
- [ ] **Step 3: Clean generated artifacts** — remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.
- [ ] **Step 4: Run final docs reconciliation** — use the neat-freak workflow to verify docs/progress/README/AGENTS alignment, including the markdown-gate scope note now that it covers Parts 1-6.
- [ ] **Step 5: Dispatch a whole-branch review and mark R6 complete** — dispatch a final whole-branch code-reviewer, triage its findings, then only after fresh verification mark R6 complete and commit the final docs sync.

## Exit Criteria

- Part 6 Chapter/Lab/Solution are rewritten around the "defend the build-vs-adopt decision with a pinned task/fixture/metric" problem, with the technical-selection mental model present.
- Chapter 06 has at least two ASCII diagrams (harness flow and weighted-score computation) and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- The rewrite makes the weighted score transparent (manual reproduction of a `total_score`, plus the `>=0.8` strengths / `<0.55` tradeoffs derivation and the deterministic tie-break), which the v1 material never did.
- Lab 06 includes L1 Follow, L2 Modify, and L3 Design exercises with full Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback for each.
- Solution 06 explains what each assertion proves and why the design matters, including why the handwritten baseline stays the product/teaching baseline.
- Every error-demonstrating block self-catches, and the markdown Python block gate covers Part 6 (Parts 1-6) with no infra/gate helper change.
- `course/README.md`, `README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R6 status while Part 7 remains marked as current v1 material.
- No `course/framework_comparisons/common.py`, `packages/`, `apps/`, or `infra/` code changed.
- Every changed code block was re-run against the real `course.framework_comparisons` API and matched documented output exactly.
- Final verification and a whole-branch review are recorded in `docs/progress/phases/phase-r6.md` and `docs/progress/overall.md`.

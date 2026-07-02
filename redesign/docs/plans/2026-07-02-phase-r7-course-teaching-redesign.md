# Phase R7: Part 7 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite Part 7 so Production Readiness teaches local-first production boundaries — diagnostics, JSONL persistence, approval policy, sandbox policy, and docs freshness — through the local paper research assistant's "can we replay, audit, and block unsafe runs before real deployment?" problem, using the project-driven teaching contract established in Phases R1-R6.

**Architecture:** No runtime/product code changes are expected. R7 rewrites `course/chapters/07-production-readiness.md`, `course/labs/07-production-readiness-lab.md`, and `course/solutions/07-production-readiness-solution.md`; adds the three Part 7 files to the markdown Python block gate's `COURSE_MARKDOWN_PATHS`; and updates the docs/progress surfaces that index them. The rewrite uses the existing `research_core.production` contracts: `RunDiagnostics`, `JsonlRunEventStore`, `ApprovalMode`, `ApprovalPolicy`, `ApprovalRule`, `ApprovalDecision`, `SandboxPolicy`, `SandboxDecision`, and `JSONL_EVENT_LOG_SCHEMA_VERSION`, plus the existing docs freshness gate in `infra.docs_freshness`.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`, pytest/ruff, and the existing markdown Python block gate.

---

## First-Principles Review

R6 completed the Part 6 Framework Comparisons rewrite and the markdown Python block gate covered setup material plus Parts 1-6 at R7 planning time. Runtime/product Phase 7 was already implemented and marked complete: `research_core.production` contained offline production-readiness contracts, the docs freshness gate existed, and Course 07 had pre-rewrite teaching material. R7 is not a new product/runtime phase; it is a teaching rewrite phase for Part 7, the same kind of work R2-R6 performed for Parts 2-6.

Reading the current Part 7 files against the Part Contract in `docs/course/roadmap.md` shows concrete teaching gaps:

- The chapter opens with a generic "Goal" and "The Idea In Plain Language"; it does not start from the concrete production problem: the local paper research assistant can now run, cite, remember, delegate, show a workbench, and compare frameworks, but before real deployment the team needs to answer "if a run goes wrong, can we replay it, audit it, and block unsafe actions?"
- There is no Learner Contract block. Learners do not get the standard "Who this is for / Before you start / You will build / You will be able to explain / You will prove it works by running / Offline guarantee" promise used by the rewritten Parts.
- The pre-rewrite mental model was underdeveloped. It listed four contracts, but did not map them to a plain-language production boundary: `RunDiagnostics` = incident summary, `JsonlRunEventStore` = black-box recorder, `ApprovalPolicy` = human approval gate for tool subjects, `SandboxPolicy` = local file/network fence, and docs freshness = trust boundary for course/project navigation.
- The pre-rewrite examples were runnable but flat. They showed the happy path for diagnostics, JSONL, approval, and sandbox decisions, but did not walk through a full Build -> Inspect -> Break -> Fix -> Reflect loop where a learner builds the run record, inspects what survives, breaks the boundaries, fixes the inputs, and explains why the failure is good.
- Lab 07 has four exercises, but it does not use the standard L1 Follow / L2 Modify / L3 Design progression or the four-part feedback loop (Common Errors, Failure Output Interpretation, Where To Go Back, Why Correct Answer Is Correct).
- Solution 07 has runnable answers, but it does not consistently include "What This Proves" and "Why This Design" sections per tier, and it does not frame L3 as one valid production-readiness policy design with required invariants.
- There are no ASCII diagrams and no stable callouts (`[DD]`, `[TRAP]`, `[CHECK]`, `[BIG]`, `[DEEP]`), so learners do not get the visual system map R2-R6 now provide.
- The current Chapter 07 v1 "Failure Lab Preview" originally raised `ValueError` uncaught for `access="execute"`. This was fixed in the R6 post-audit sync so the block self-catches, but R7 still needs to normalize every error-demonstrating block across chapter/lab/solution before adding Part 7 to the gate.
- Part 7 is the last teaching Part before Capstone. It must explicitly connect backward to Parts 1-6 and forward to R8: Capstone should be able to reuse the same event trail, evidence chain, memory panel, delegation trail, workbench snapshot, framework comparison record, and production-readiness decisions.

I verified the real `research_core.production` behavior the rewrite will teach:

```python
# 1. RunDiagnostics requires a non-empty, single-run event tuple.
RunDiagnostics.from_events(())  # -> ValueError: events must not be empty
RunDiagnostics.from_events((event_for_run_1, event_for_run_2))
# -> ValueError: events must belong to one run_id

# 2. JsonlRunEventStore preserves append order and exposes run_id-based replay.
store.append_many(events)
store.list_run_ids()                   # -> ("run_7",)
[event.id for event in store.read_run("run_7")]
# -> ["evt_1", "evt_2", "evt_3", "evt_4"]
store.read_run("missing")              # -> ()

# 3. ApprovalPolicy is first-match wins, then default mode.
approval.decide("retriever.search").mode       # -> ApprovalMode.ALLOW
approval.decide("shell.exec").mode             # -> ApprovalMode.DENY
approval.decide("email.send").requires_review  # -> True

# 4. SandboxPolicy has explicit file/network decisions.
sandbox.decide_path(workspace / "notes.md", access="read").allowed            # -> True
sandbox.decide_path(workspace / "outputs/report.md", access="write").allowed  # -> True
sandbox.decide_path(workspace / "secrets/token.txt", access="read").allowed   # -> False
sandbox.network_decision().allowed                                             # -> False
sandbox.decide_path(workspace / "script.sh", access="execute")
# -> ValueError: access must be one of: read, write
```

I also verified the gate constraint. Part 7 imports only `research_core.production` and `research_core.runtime`, so it should work under the existing markdown gate path. After the R6 post-audit sync, the direct gate probe on the three v1 Part 7 files no longer needs any helper path change; the remaining R7 gate work is to add the three files to `COURSE_MARKDOWN_PATHS` after rewriting them into the new teaching shape and confirming every error block self-catches.

Therefore R7 should not modify `packages/research_core/production`, `infra/docs_freshness.py`, `apps/`, or runtime/product code unless implementation discovers a real inconsistency between documented behavior and tests. The existing production contracts are already enough for a full project-driven teaching rewrite. The phase succeeds when Part 7 follows the same rhythm as Parts 2-6:

- problem hook: "你的本地论文研究助手快要交给别人用了。现在问题不是它能不能回答，而是出事后能不能复盘、记录能不能保存、危险动作能不能被挡住、文档索引能不能信。"
- mental model: production readiness = local-first safety desk. `RunDiagnostics` is the incident summary; `JsonlRunEventStore` is the black-box recorder; `ApprovalPolicy` is the human approval gate; `SandboxPolicy` is the local file/network fence; docs freshness is the map-checker that keeps learners and agents from following broken links.
- at least two ASCII diagrams: (a) `RunEvent trajectory -> RunDiagnostics -> JsonlRunEventStore -> replay/audit`, and (b) `tool request/path/network -> ApprovalPolicy/SandboxPolicy -> allow/deny/require_approval decision record`.
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop: build a small failed run trajectory, inspect diagnostics and JSONL replay, break empty/mixed run inputs plus invalid sandbox access, fix the inputs, and explain why refusing bad data is production readiness.
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops. L3 should ask learners to design a production-readiness policy for a new local research scenario and prove required invariants (diagnostics single-run, JSONL replay, approval defaults, sandbox blocked paths, network decision).
- a forward connection to R8 Capstone: the final project must ship with a saved event trail, a diagnostics summary, approval/sandbox decisions, and a readiness checklist before a report can be trusted.

## Global Constraints

- Do not modify `packages/research_core/production`, `packages/research_core/runtime`, `apps/`, or `infra/docs_freshness.py` unless a verified code/documentation mismatch is found during implementation.
- Do not introduce real cloud logging, databases, OAuth/auth providers, queues, live network calls, real provider SDKs, or deployment automation.
- Keep production readiness local-first and offline: the course teaches contracts that future infrastructure can wrap, not infrastructure itself.
- Use only the existing `research_core.production` public API and tested behavior.
- Keep all Python snippets runnable from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python`.
- Every error-demonstrating Python block must self-catch (`try/except`) so the markdown Python block gate does not abort.
- Add the three Part 7 files to `tests/course/test_markdown_python_blocks.py` only after the chapter/lab/solution are gate-clean.
- Keep Capstone labeled as planned R8 and reference/support materials labeled as planned R9.
- Update `docs/progress/` after each landed task or milestone.
- Commit each milestone with a detailed commit message and push to GitHub after each meaningful milestone, matching the R1-R6 workflow.

## File Map

Create:

- `docs/progress/phases/phase-r7.md`

Modify:

- `tests/course/test_markdown_python_blocks.py` (add the three Part 7 files to `COURSE_MARKDOWN_PATHS`)
- `course/chapters/07-production-readiness.md`
- `course/labs/07-production-readiness-lab.md`
- `course/solutions/07-production-readiness-solution.md`
- `course/README.md`
- `README.md`
- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `docs/operations/production-readiness.md` and `infra/local-readiness-checklist.md` only if the Part 7 rewrite reveals stale wording about what the course asks learners to verify

## Task 1: Start R7 Plan And Progress

**Files:**

- Create: `docs/progress/phases/phase-r7.md`
- Modify: `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/README.md`, `docs/progress/overall.md`, `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Confirm the starting branch** — create or switch to `codex/redesign-course-r7` from the current R6 completion branch.
- [ ] **Step 2: Add this plan to indexes** — ensure this file is linked from `docs/README.md`, `docs/course/roadmap.md`, and the execution roadmap before implementation starts.
- [ ] **Step 3: Start progress tracking** — create `docs/progress/phases/phase-r7.md` with R7 scope, task checklist, exit signal, verification target, and a start log dated with the actual start date.
- [ ] **Step 4: Update overall progress** — mark R7 active without claiming Part 7 is rewritten yet. Keep Capstone as planned R8 and references as planned R9.
- [ ] **Step 5: Verify indexed docs paths** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: docs freshness passes.
- [ ] **Step 6: Commit and push** — commit the plan/progress kickoff on `codex/redesign-course-r7` and push the branch.

## Task 2: Rewrite Chapter 07

**Files:**

- Modify: `course/chapters/07-production-readiness.md`
- Modify: `docs/progress/phases/phase-r7.md`

- [ ] **Step 1: Rewrite opener and learner contract** — turn Chapter 07 into "Part 7: Production Readiness" with a Learner Contract block matching Parts 2-6.
- [ ] **Step 2: Open with the problem hook** — start from the assistant being almost ready for handoff, but the team cannot trust it until a run can be replayed, audited, and bounded by approval/sandbox decisions.
- [ ] **Step 3: Introduce the mental model** — production readiness = local-first safety desk. Map `RunDiagnostics`, `JsonlRunEventStore`, `ApprovalPolicy`, `SandboxPolicy`, and docs freshness to their plain-language jobs.
- [ ] **Step 4: Add architecture diagrams** — include at least two ASCII diagrams: event replay (`RunEvent -> diagnostics -> JSONL -> replay`) and policy gate (`tool/path/network request -> approval/sandbox -> decision record`).
- [ ] **Step 5: Build and inspect the run record** — construct the four-event `run_7` trajectory, print `RunDiagnostics.to_record()`, write/read via `JsonlRunEventStore`, and show exactly what survives for audit.
- [ ] **Step 6: Teach approval and sandbox boundaries** — demonstrate first-match approval decisions, default `require_approval`, blocked path precedence, and disabled network decisions with concrete printed records.
- [ ] **Step 7: Break and fix the production boundary** — self-catch and diagnose `events must not be empty`, `events must belong to one run_id`, invalid event log schema, blank approval subject, invalid sandbox access, blocked path, and disabled network decisions. Explain which boundary each failure protects.
- [ ] **Step 8: Add product/course connection and eval gate** — connect Part 7 back to Parts 1-6 and forward to R8 Capstone. List focused production tests, docs freshness, markdown block gate, full pytest, ruff, and web build commands.
- [ ] **Step 9: Add reflection questions** — include tradeoff questions about why local contracts precede cloud infra, why JSONL is enough for the course, and what would need to change before real auth/database/cloud deployment.
- [ ] **Step 10: Direct gate self-check** — run `PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/07-production-readiness.md --project-root .`. Expected: every chapter Python block executes and every adjacent `Expected output:` matches.
- [ ] **Step 11: Commit and push** — commit the chapter rewrite and progress update, then push.

## Task 3: Rewrite Lab 07

**Files:**

- Modify: `course/labs/07-production-readiness-lab.md`
- Modify: `docs/progress/phases/phase-r7.md`

- [ ] **Step 1: Convert lab to L1/L2/L3** — L1 Follow builds diagnostics and JSONL replay from the provided `run_7`; L2 Modify changes the trajectory and policy rules, predicts then verifies diagnostics/policy decisions; L3 Design creates a new production-readiness boundary for a local report-export scenario.
- [ ] **Step 2: Add feedback loops** — every tier includes Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct.
- [ ] **Step 3: Add break/fix checks** — include empty events, mixed run IDs, invalid JSONL schema, blank approval subject, invalid sandbox access, blocked path, and network disabled checks. Every exception block must self-catch.
- [ ] **Step 4: Make L3 open-ended but verifiable** — the lab should state required invariants instead of pretending there is one canonical policy: diagnostics must be single-run, JSONL replay must preserve event order, unknown external actions must require approval or deny, secrets must be blocked, and network must be explicit.
- [ ] **Step 5: Direct gate self-check** — run `PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/labs/07-production-readiness-lab.md --project-root .`. Expected: every lab Python block executes and every adjacent `Expected output:` matches.
- [ ] **Step 6: Commit and push** — commit the lab rewrite and progress update, then push.

## Task 4: Rewrite Solution 07

**Files:**

- Modify: `course/solutions/07-production-readiness-solution.md`
- Modify: `docs/progress/phases/phase-r7.md`

- [ ] **Step 1: Provide runnable answers** — include complete L1/L2/L3 solution snippets with `assert`-based self-verification so the markdown gate executes them.
- [ ] **Step 2: Explain why answers are correct** — for each tier add "What This Proves" and "Why This Design", matching Solutions 02-06.
- [ ] **Step 3: State L3 as one valid design** — provide one reference production-readiness policy design plus required invariants, not a fake single right answer.
- [ ] **Step 4: Connect forward to Capstone** — explain how R8 should use saved event logs, diagnostics, approval/sandbox records, and docs freshness as part of the final project's trust boundary.
- [ ] **Step 5: Direct gate self-check** — run `PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/solutions/07-production-readiness-solution.md --project-root .`. Expected: every solution Python block executes and every adjacent `Expected output:` matches.
- [ ] **Step 6: Commit and push** — commit the solution rewrite and progress update, then push.

## Task 5: Add Part 7 To The Gate And Sync Indexes

**Files:**

- Modify: `tests/course/test_markdown_python_blocks.py`
- Modify: `course/README.md`, `README.md`, `docs/README.md`, `docs/course/roadmap.md`, `docs/plans/2026-06-25-redesign-execution-roadmap.md`, `docs/progress/README.md`, `docs/progress/overall.md`, `docs/progress/phases/phase-r7.md`

- [ ] **Step 1: Add Part 7 files to the gate** — append the three Part 7 chapter/lab/solution paths to `COURSE_MARKDOWN_PATHS`. No helper change should be needed because Part 7 imports from `research_core.production`.
- [ ] **Step 2: Run the markdown gate** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q`. Expected: passes with Parts 0-7 included.
- [ ] **Step 3: Mark Part 7 as R7 rewritten** — update course indexes to describe Part 7 as completed R7 material. Keep Capstone planned R8 and reference/support material planned R9.
- [ ] **Step 4: Verify docs freshness** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: passes with all indexed paths resolved.
- [ ] **Step 5: Commit and push** — commit gate/index/progress sync and push.

## Task 6: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`, `docs/progress/phases/phase-r7.md`

- [ ] **Step 1: Run final verification** — run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [ ] **Step 2: Run the direct Part 7 gate** — run `PYTHONPATH=.:packages/research_core/src uv run python -m infra.markdown_python_blocks course/chapters/07-production-readiness.md course/labs/07-production-readiness-lab.md course/solutions/07-production-readiness-solution.md --project-root .`. Expected: all Part 7 blocks execute and expected outputs match.
- [ ] **Step 3: Clean generated artifacts** — remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.
- [ ] **Step 4: Run final docs reconciliation** — use the neat-freak workflow to verify docs/progress/README/AGENTS alignment, including the markdown-gate scope note now that it covers Parts 0-7.
- [ ] **Step 5: Dispatch a whole-branch review and mark R7 complete** — run a whole-branch review, triage its findings, then only after fresh verification mark R7 complete and commit the final docs sync.
- [ ] **Step 6: Commit and push** — commit final verification/progress/docs reconciliation and push.

## Exit Criteria

- Part 7 Chapter/Lab/Solution are rewritten around the "replay, audit, and block unsafe runs before real deployment" problem, with the local-first safety-desk mental model present.
- Chapter 07 has at least two ASCII diagrams and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- The rewrite teaches diagnostics, JSONL event replay, approval policy, sandbox policy, and docs freshness as inspectable local contracts before cloud/auth/database infrastructure.
- Lab 07 includes L1 Follow, L2 Modify, and L3 Design exercises with full Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback for each.
- Solution 07 explains what each assertion proves and why the design matters, including one valid L3 reference design and required production-readiness invariants.
- Every error-demonstrating block self-catches, and the markdown Python block gate covers Part 7 with no helper change.
- `course/README.md`, `README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R7 status while Capstone remains planned R8 and support references remain planned R9.
- No `packages/research_core`, `apps`, or `infra` code changes landed unless backed by a verified mismatch and focused tests.
- Every changed code block was run against the real `research_core.production` API and matched documented output exactly.
- Final verification and a whole-branch review are recorded in `docs/progress/phases/phase-r7.md` and `docs/progress/overall.md`.

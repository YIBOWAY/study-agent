# Phase R5: Part 5 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Rewrite Part 5 so Workbench Product teaches the product-adapter boundary (raw domain objects -> `WorkbenchSnapshot` -> FastAPI read API -> React panels) through the local paper research assistant's "the researcher cannot read code, give them an inspectable workbench" problem, using the project-driven teaching contract established in Phases R1-R4.

**Architecture:** No runtime/product code changes to the contracts themselves. R5 rewrites `course/chapters/05-workbench-product.md`, `course/labs/05-workbench-product-lab.md`, `course/solutions/05-workbench-product-solution.md`; extends the markdown Python block gate so it can execute Part 5 core-product blocks (and, if adopted, API blocks) and adds the Part 5 files to the checked set; and updates the docs/progress surfaces that index them. The rewrite uses the existing `research_core.product` contracts: `WorkbenchProject`, `WorkbenchRun`, `WorkbenchTimelineItem`, `WorkbenchDelegationNode`, `WorkbenchEvidenceItem`, `WorkbenchSourceItem`, `WorkbenchReport`, `WorkbenchMemoryItem`, `WorkbenchSkillItem`, `WorkbenchEvalItem`, `WorkbenchSnapshot`, their `from_*` adapter classmethods, and `build_demo_workbench_snapshot`, plus the existing `apps/api` FastAPI app and `apps/web` React app.

**Tech Stack:** Markdown, ASCII diagrams, Python shell snippets run from `redesign/` with `PYTHONPATH=packages/research_core/src uv run python` (and, for API snippets, `PYTHONPATH=apps/api/src:packages/research_core/src uv run python`), plus the existing Vite/React build for `apps/web`.

---

## First-Principles Review

R4 completed the Part 4 teaching rewrite and extended the automated markdown Python block gate (`infra/markdown_python_blocks.py` + `tests/course/test_markdown_python_blocks.py`) to cover Parts 1-4. The current Part 5 files (`chapters/05-workbench-product.md`, `labs/05-workbench-product-lab.md`, `solutions/05-workbench-product-solution.md`) are still v1 material. Reading them against the Part Contract in `docs/course/roadmap.md` shows concrete gaps, not just a style mismatch:

- No Learner Contract block and no Problem Hook narrative. The chapter opens with a "Goal" section, not the concrete moment a researcher says "I cannot read code; give me something I can open and inspect."
- No mental-model analogy. There is no "the product layer is the researcher's dashboard, and the snapshot is the single stable page contract" story mapping the `Workbench*` objects to plain-language roles, the way Part 2 used a detective story, Part 3 used a notebook and a skill backpack, and Part 4 used a delegated helper.
- Only `build_demo_workbench_snapshot()` and `to_record()` are demonstrated. The `from_event`, `from_evidence`, `from_source`, `from_report`, and `from_memory_record` adapter classmethods — which are the actual mechanism that turns raw domain objects (`RunEvent`, `Source`, `Evidence`, `Report`, `MemoryRecord`) into product items — are never shown. Learners see the finished demo snapshot but never build one from raw objects, so the "adapter" concept that is the whole point of the Part is invisible.
- The snapshot's referential-integrity validation (`_validate_snapshot_references`) is never taught or broken. This validation is exactly the "the product contract protects the UI" guarantee the Part should showcase, and it is rich: `run.project_id` must match `project.id`, timeline `run_id` must match `run.id`, report `run_id` must match `run.id`, report `claim_source_links` `evidence_id` must reference snapshot evidence, delegation node ids must be unique, delegation `parent_id` must reference another node, and source evidence `source_id` must match its source. None of these failure paths appear in the v1 material.
- `summary_row()` on `WorkbenchMemoryItem` / `WorkbenchSkillItem` / `WorkbenchEvalItem` is only shown incidentally for memory and is never explained as the "list-row projection the UI renders."
- The v1 Break/Fix is minimal: one mutate-the-record copy proof and one bad eval score. It never breaks the cross-reference validations, which are the most instructive failures.
- Lab 05 has flat "Exercise 1-4" blocks with no L1/L2/L3 tiering and no Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback loop.
- There are no ASCII diagrams and no `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts anywhere in the current Part 5 material.

I verified the parts of the real `research_core.product` and `apps/api` API that the current v1 material does not exercise, so the rewrite has accurate new material to draw on (all outputs below were confirmed by running the exact snippets from `redesign/`):

```python
# 1. from_event turns a raw RunEvent into a product timeline item (adapter mechanism v1 never shows).
WorkbenchTimelineItem.from_event(
    RunEvent(id="e1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload={"tokens": {"prompt": 5}}),
    title="Model request",
).type.value
# -> 'model_request'   (metadata carries the event payload)

# 2. Referential integrity is enforced at snapshot construction, not in the UI:
WorkbenchSnapshot(project=WorkbenchProject(id="p1", title="P"),
                  run=WorkbenchRun(id="r1", project_id="WRONG", title="R", question="q"))
# -> ValueError: run project_id must match project id

WorkbenchSnapshot(project=..., run=WorkbenchRun(id="r1", project_id="p1", ...),
                  timeline=[WorkbenchTimelineItem(id="t1", run_id="OTHER", type=RunEventType.MODEL_REQUEST, title="x")])
# -> ValueError: timeline run_id must match run id

WorkbenchSnapshot(..., delegation=[node_d1, another_node_also_d1])
# -> ValueError: delegation node ids must be unique

WorkbenchEvalItem(id="e", title="t", metric="m", status="passed", score=1.5)
# -> ValueError: score must be a number between 0 and 1

# 3. build_demo_workbench_snapshot() exposes exactly nine panels:
sorted(build_demo_workbench_snapshot().to_record().keys())
# -> ['delegation', 'evals', 'memory', 'project', 'report', 'run', 'skills', 'sources', 'timeline']

# 4. The FastAPI transport returns the same record shape (needs apps/api/src on the path):
#    PYTHONPATH=apps/api/src:packages/research_core/src
from research_api.main import create_app
TestClient(create_app()).get("/health").json()
# -> {'status': 'ok', 'service': 'research-workbench-api'}
```

I also verified one gate-relevant constraint that shapes Task 2 below. The current markdown gate helper `_ensure_research_core_on_path` only adds `packages/research_core/src` to `sys.path`. Confirmed by running:

```text
PYTHONPATH=packages/research_core/src  ->  from research_api.main import create_app
# -> ModuleNotFoundError: No module named 'research_api'
```

So Part 5's API-dependent blocks (the `TestClient` exercises) cannot be added to the markdown gate unchanged; the gate would need `apps/api/src` on `sys.path` too, or those blocks must stay as non-executed documentation. This is the central design decision of R5's gate task, analogous to R3 introducing the gate and R4 backfilling it.

Therefore R5 should not change the `research_core.product` contracts or the `apps/api` / `apps/web` code. The existing product surface already has enough depth (adapters + referential validation + three-layer boundary) for a full Part Contract rewrite; the current material simply teaches the finished demo without the adapter mechanism or the protective validations. The phase succeeds when Part 5 follows the same rhythm as Parts 1-4:

- problem hook: "研究员说：我看不懂代码，也看不懂 event trail 的原始 dict。给我一个能打开、能点、能核对出处的工作台。" then the failure to avoid: if the UI invents its own data model, or reads live internal objects, the workbench and the runtime start telling different stories;
- mental model: product layer = 研究员的仪表盘；`WorkbenchSnapshot` = 一页稳定的页面契约（不是把后端对象原样丢给前端）；`from_*` adapters = 把工程对象翻译成产品面板项；referential validation = 契约在替 UI 守边界；三层边界 core product -> FastAPI transport -> React panels 只能自上而下依赖;
- at least one full Build -> Inspect -> Break -> Fix -> Reflect loop, where Build assembles a snapshot from raw `Source`/`Evidence`/`Claim`/`Report`/`RunEvent`/`MemoryRecord` via the `from_*` adapters, Inspect reads `to_record()` panels and `summary_row()` projections, and Break/Fix triggers the referential-integrity errors;
- L1 Follow, L2 Modify, and L3 Design exercises with feedback loops, including an L3 that asks the learner to assemble a *new* valid snapshot from scratch for a different research scenario (their own sources/evidence/claims/timeline) and prove the cross-references hold and `to_record()` returns independent copies — achievable with existing contracts and no new product code;
- at least two ASCII diagrams: (a) a three-layer boundary/data-flow diagram (`raw domain objects -> from_* adapters -> WorkbenchSnapshot.to_record() -> FastAPI read endpoints -> React panels`, with the dependency arrow pointing only downward), and (b) an object-composition diagram of `WorkbenchSnapshot` showing its nine panel slots and which raw object each panel item adapts from;
- a section that inspects the FastAPI transport with `TestClient` and the React fallback-fixture contract (fallback must match the API record shape), tying the "no separate data model in the UI" rule to a `[DD]` callout;
- offline verification only (no API key, no network, no real provider); the React build stays a separate `npm run build` verification.

## Global Constraints

- Do not modify the `research_core.product` contracts, `apps/api/src`, or `apps/web/src` application code in this phase. Teaching-only changes.
- The one permitted non-course code change is a minimal, principled extension of `infra/markdown_python_blocks.py` to also place `apps/api/src` on `sys.path` when it exists (see Task 2), so API code blocks can execute. If that extension is not adopted, API-dependent blocks must remain non-executed documentation and be covered by `tests/apps/test_workbench_api.py` instead; do not silently weaken the gate.
- Do not introduce real auth, databases, websockets, streaming, real providers, or network calls.
- Use only existing `research_core.product` contracts and `from_*` adapters; do not add new `Workbench*` fields, methods, or panel types.
- Keep all Python snippets runnable from `redesign/`. Core-product snippets use `PYTHONPATH=packages/research_core/src`; API snippets use `PYTHONPATH=apps/api/src:packages/research_core/src`. State the required path at the top of each snippet group.
- Keep Parts 6-7 labeled as current v1 material until their own R6-R7 rewrites land.
- Update `docs/progress/` after each landed task or milestone.
- Commit each milestone with a detailed commit message. Push only when the user approves pushing.

## File Map

Create:

- `docs/progress/phases/phase-r5.md`

Modify:

- `infra/markdown_python_blocks.py` (extend `sys.path` setup to include `apps/api/src` when present; see Task 2)
- `tests/course/test_markdown_python_blocks.py` (add Part 5 files to the checked set)
- `docs/README.md`
- `docs/course/roadmap.md`
- `docs/progress/README.md`
- `docs/progress/overall.md`
- `docs/plans/2026-06-25-redesign-execution-roadmap.md`
- `course/README.md`
- `course/chapters/05-workbench-product.md`
- `course/labs/05-workbench-product-lab.md`
- `course/solutions/05-workbench-product-solution.md`
- `AGENTS.md` and `infra/local-readiness-checklist.md` (only if the gate scope note needs updating for Part 5 / apps path)

## Task 1: Start R5 Plan And Progress

**Files:**

- Create: `docs/progress/phases/phase-r5.md`
- Modify: `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/README.md`, `docs/progress/overall.md`, `docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add this plan** — save this plan under `docs/plans/` (already done by this authoring step).
- [x] **Step 2: Start progress tracking** — create `docs/progress/phases/phase-r5.md` with R5 scope, task checklist, verification target, and a start log dated with the actual start date.
- [x] **Step 3: Update indexes** — update the docs/progress indexes and the execution roadmap so R5 is visible as active, without marking rewritten course content complete yet.
- [x] **Step 4: Verify indexed docs paths** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: docs freshness passes.
- [x] **Step 5: Commit** — commit the plan/progress kickoff on a phase branch (for example `codex/redesign-course-r5`).

## Task 2: Extend The Markdown Python Block Gate For Part 5

**Files:**

- Modify: `infra/markdown_python_blocks.py`
- Modify: `tests/course/test_markdown_python_blocks.py`
- Modify: `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Decide the API-block strategy (design decision)**

Part 5 is the first Part whose code blocks need a second source root (`apps/api/src`) on top of `packages/research_core/src`. Choose and record one approach:

- Preferred: extend `_ensure_research_core_on_path` (or add a sibling helper) so that when `apps/api/src` exists under the project root, it is also inserted on `sys.path`. This mirrors the exact `PYTHONPATH` the course tells learners to use and keeps the "every executable block actually runs" guarantee for Part 5's API exercises.
- Fallback: keep API-dependent blocks (`TestClient`, `from research_api.main import create_app`) as `text`/documentation blocks that the gate does not execute, and rely on `tests/apps/test_workbench_api.py` for API correctness. Record this as an explicit exclusion, not a silent gap.

- [x] **Step 2: Implement the chosen approach (TDD)**

If extending the path: add the helper, then add the three Part 5 files to `COURSE_MARKDOWN_PATHS`. Write/adjust a gate test first so a Part 5 API block would fail before the fix and pass after. Confirm the extension does not change behavior for Parts 1-4 (they only need `packages/research_core/src`).

- [x] **Step 3: Verify the gate**

Run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q`. Expected: passes for all included files, now including Part 5. Note: because the gate itself must import `research_api`, confirm the gate test passes under the plain `pytest` invocation used in CI (the helper must add the path, not rely on the caller's `PYTHONPATH`).

## Task 3: Rewrite Chapter 05

**Files:**

- Modify: `course/chapters/05-workbench-product.md`
- Modify: `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Rewrite opener and learner contract** — turn Chapter 05 into "Part 5: Workbench Product" with a Learner Contract block (Who this is for / Before you start / You will build / You will be able to explain / You will prove it works by running / Offline guarantee), matching Chapter 02-04, and update the project progress tracker so Part 4 is `[x]` and Part 5 is `[*]`.
- [x] **Step 2: Open with the problem hook** — start from the researcher who cannot read code or raw event dicts and needs an inspectable workbench. Name the two failures to avoid: the UI inventing its own data model, and the UI reading live internal objects that drift from the runtime.
- [x] **Step 3: Introduce the mental model** — product layer = 研究员的仪表盘; `WorkbenchSnapshot` = 一页稳定的页面契约; `from_*` adapters = 工程对象到面板项的翻译; referential validation = 契约替 UI 守边界. Use a story-role/panel table mapping each `Workbench*` item to the raw object it adapts from and the panel it feeds.
- [x] **Step 4: Add architecture and composition diagrams** — add at least two ASCII diagrams: (a) the three-layer downward-only data flow (`raw domain objects -> from_* adapters -> WorkbenchSnapshot.to_record() -> FastAPI -> React panels`), and (b) a `WorkbenchSnapshot` composition diagram showing its nine panel slots and their source objects.
- [x] **Step 5: Build a snapshot from raw objects and inspect it** — instead of only calling `build_demo_workbench_snapshot()`, walk the learner through assembling a small snapshot from raw `Source`/`Evidence`/`Claim`/`Report`/`RunEvent`/`MemoryRecord` using the `from_*` adapters. Inspect `to_record()` panels, `summary_row()` projections, and the timeline order. Keep `build_demo_workbench_snapshot()` as a reference base case.
- [x] **Step 6: Break and fix the referential integrity** — trigger and diagnose the real validation errors: `run project_id must match project id`, `timeline run_id must match run id`, `report claim_source_links evidence_id must reference snapshot evidence`, `delegation node ids must be unique`, and `score must be a number between 0 and 1`. Frame each as Break -> diagnose from the message -> Fix, and explain that the contract fails at construction so a broken snapshot can never reach the UI.
- [x] **Step 7: Inspect the transport and UI boundary** — show the FastAPI `TestClient` reading `/health`, `/api/workbench/snapshot`, and `/api/workbench/timeline`, and the mutate-the-record copy-safety proof. Explain the React fallback-fixture-must-match-shape rule with a `[DD]` callout. Note the required `PYTHONPATH=apps/api/src:packages/research_core/src` for API snippets.
- [x] **Step 8: Add product connection and eval gate** — explain how every earlier Part's objects surface here (Part 1 events -> timeline, Part 2 evidence chain -> sources/report, Part 3 memory -> memory panel, Part 4 delegation -> delegation tree) and forward to Part 7 (a production run must be reconstructable from the same records). List the exact pytest/ruff commands plus `tests/course/test_markdown_python_blocks.py` and the `cd apps/web && npm run build` check.
- [x] **Step 9: Add reflection questions** — include at least one tradeoff question, for example: why enforce referential integrity in the Python snapshot contract instead of in React validation, and what breaks if the UI is the only place that checks it?

## Task 4: Rewrite Lab 05

**Files:**

- Modify: `course/labs/05-workbench-product-lab.md`
- Modify: `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Convert lab to L1/L2/L3** — L1 Follow: inspect `build_demo_workbench_snapshot().to_record()` panels and call the API with `TestClient`. L2 Modify: predict-then-verify — mutate a returned record and prove the fresh snapshot is unchanged; change one raw object so a `from_*`-built snapshot fails a specific referential check. L3 Design: no skeleton; assemble a *new* valid snapshot from scratch for a different research scenario using the `from_*` adapters, and prove the required invariants (nine panels present, cross-references valid, `to_record()` returns independent copies, `summary_row()` projections correct).
- [x] **Step 2: Add feedback loops** — every exercise includes Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct, matching Lab 02-04.
- [x] **Step 3: Add break/fix checks** — include the referential-integrity failures (run/project mismatch, timeline run_id mismatch, report evidence reference, duplicate delegation ids) and the bad-eval-score failure, each with expected error text and a diagnosis question before the fix. Keep any API-dependent block consistent with the Task 2 gate decision (executed vs documentation).

## Task 5: Rewrite Solution 05

**Files:**

- Modify: `course/solutions/05-workbench-product-solution.md`
- Modify: `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Provide runnable answers** — include complete L1/L2/L3 solution snippets and assertions, covering every case introduced in Lab 05. Use `assert`-based self-verification so the markdown gate executes and checks them. Keep API snippets under the documented `apps/api/src:packages/research_core/src` path and consistent with the Task 2 decision.
- [x] **Step 2: Explain why answers are correct** — for each exercise add "What This Proves" and "Why This Design", matching Solution 02-04. For the open-ended L3, provide one reference snapshot design plus the required invariants, not a single canonical answer.
- [x] **Step 3: Connect design decisions forward** — explain why the stable snapshot contract lets FastAPI and React be replaceable shells, why referential integrity belongs in core (Part 7 diagnostics and audits depend on it), and how each earlier Part's contract (events, evidence chain, memory, delegation) shows up as a panel here.

## Task 6: Sync Course Indexes And Progress

**Files:**

- Modify: `course/README.md`, `docs/README.md`, `docs/course/roadmap.md`, `docs/progress/overall.md`, `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Mark Part 5 as R5 rewritten** — after Tasks 2-5 land, update course indexes to describe Part 5 as completed R5 material. Keep Parts 6-7 as current v1 material.
- [x] **Step 2: Verify docs freshness** — run `cd redesign && PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q`. Expected: passes with all indexed paths resolved.

## Task 7: Final Verification And Cleanup

**Files:**

- Modify: `docs/progress/overall.md`, `docs/progress/phases/phase-r5.md`

- [x] **Step 1: Run final verification** — run from `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_docs_freshness.py -q
PYTHONPATH=packages/research_core/src uv run pytest tests/course/test_markdown_python_blocks.py -q
git diff --check
cd apps/web && npm ci && npm run build
```

- [x] **Step 2: Manually re-run every new/changed course code block** — paste every changed block in Chapter 05, Lab 05, and Solution 05 into a real shell (core blocks under `PYTHONPATH=packages/research_core/src`, API blocks under `PYTHONPATH=apps/api/src:packages/research_core/src`) and confirm output matches the documented output exactly, the same way R1-R4 were verified. The gate compares stdout only for blocks with an adjacent `Expected output:` fence; blocks without one are execution-only, so a manual pass still catches output text the gate does not compare.
- [x] **Step 3: Clean generated artifacts** — remove generated `.venv`, `.pytest_cache`, `.ruff_cache`, `uv.lock`, `apps/web/node_modules`, `apps/web/dist`, `apps/web/tsconfig.tsbuildinfo`, and `__pycache__` outputs unless already tracked.
- [x] **Step 4: Run final docs reconciliation** — use the neat-freak workflow to verify docs/progress/README/AGENTS alignment, including the markdown-gate scope note now that it covers Parts 1-5 (and the `apps/api/src` path extension if adopted).
- [x] **Step 5: Mark R5 complete** — only after fresh verification, mark R5 complete and commit the final docs sync.

## Exit Criteria

- Part 5 Chapter/Lab/Solution are rewritten around the "give the researcher an inspectable workbench without inventing a separate data model" problem, with the dashboard/snapshot mental model present.
- Chapter 05 has at least two ASCII diagrams (three-layer data flow and `WorkbenchSnapshot` composition) and at least three `[DD]` / `[TRAP]` / `[CHECK]` / `[BIG]` / `[DEEP]` callouts.
- Lab 05 includes L1 Follow, L2 Modify, and L3 Design exercises with full Common Errors / Failure Output Interpretation / Where To Go Back / Why Correct Answer Is Correct feedback for each.
- The rewrite exercises the `from_*` adapters, `summary_row()` projections, and the referential-integrity validations (`run project_id`, `timeline run_id`, `report ... evidence_id`, delegation id uniqueness, eval score range), none of which the v1 material covered.
- Solution 05 explains what each assertion proves and why the design matters for Part 7 and ties the panels back to Parts 1-4.
- The markdown Python block gate covers Part 5. Either the gate executes Part 5 API blocks (via the `apps/api/src` path extension) or the API blocks are explicitly documented as gate-excluded and covered by `tests/apps/test_workbench_api.py`.
- `course/README.md`, `docs/course/roadmap.md`, `docs/README.md`, and `docs/progress/` reflect R5 status while Parts 6-7 remain marked as current v1 material.
- No `research_core.product`, `apps/api`, or `apps/web` application code changed; the only non-course code change permitted is the markdown-gate path helper in Task 2.
- Every changed code block was manually re-run against the real `research_core.product` / `apps/api` API and matched documented output exactly.
- Final verification is recorded in `docs/progress/phases/phase-r5.md` and `docs/progress/overall.md`.

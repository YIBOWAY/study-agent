# Phase R1: Part 1 Course Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform existing Chapter 00 and Chapter 01 from standalone technical documentation into Part 1 of a project-driven course, introducing the "本地论文研究助手" narrative thread and establishing the new teaching methodology (three-tier exercises, feedback loops, ASCII diagrams, `[DD]`/`[TRAP]`/`[CHECK]`/`[BIG]` callouts, and the Build→Inspect→Break→Fix→Reflect cycle).

**Architecture:** No runtime/product code changes. All changes are within `course/` (markdown rewrites) and `docs/` (template, roadmap, index, progress). Files keep `chapters/00-07` naming; content uses "Part 1" in titles. Each chapter/lab/solution rewrite follows the new template from `docs/course/chapter-template.md`.

**Tech Stack:** Markdown, ASCII art, Python shell snippets (existing `research_core` APIs only).

---

## Global Constraints

- No changes to `packages/research_core`, `apps/api`, `apps/web`, or `tests/`.
- All examples must run offline with `PYTHONPATH=packages/research_core/src uv run python` and `FakeModel`.
- Callouts use ASCII tags (`[DD]`, `[TRAP]`, `[CHECK]`, `[BIG]`) as primary markers; emoji optional.
- Files keep `chapters/`, `labs/`, `solutions/` directory names (no rename to `parts/`).
- Narrative uses "本地论文研究助手" (offline, static paper fixtures, FakeRetriever, no real API).
- Every L1/L2/L3 exercise must include: Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct.
- Verification: `uv run pytest -q` and `uv run ruff check .` must pass after all changes.
- R1 only restructures Part 1 and the learner entrypoint. Parts 2-7 remain valid v1 material until their R2-R7 rewrites land; indexes must label them as "current v1 material" rather than implying the full course already uses the new Part method.
- Verification status must never be pre-marked as passing. Mark quality gates only after reading the rewritten files and running the stated commands.
- After each committed milestone, push the active branch with `git push origin HEAD` so GitHub reflects the current progress.
- Commit messages must describe the actual change and must not include inaccurate co-author trailers.

---

## File Map

```
Create:
  course/capstone/README.md                              # Capstone placeholder

Modify:
  docs/course/chapter-template.md                         # Replace with new template
  docs/course/roadmap.md                                  # Update to Part structure
  docs/README.md                                          # Add R1 entries to index
  docs/progress/overall.md                                # Add Phase R1 to dashboard
  docs/progress/phases/phase-r1.md                        # Create R1 progress record
  course/chapters/00-before-agent-kernel.md               # Rewrite as Part 1 Section 1
  course/chapters/01-agent-kernel-foundations.md           # Rewrite as Part 1 Sections 2-5
  course/labs/01-agent-runner-lab.md                      # Rewrite as three-tier + feedback
  course/solutions/01-agent-runner-solution.md             # Add design rationale + "why correct"
  course/README.md                                        # Rewrite as project-driven guide
```

---

### Task 1: Create Capstone Placeholder

**Files:**
- Create: `course/capstone/README.md`

**Interfaces:**
- Consumes: nothing
- Produces: `course/capstone/README.md` — placeholder that `course/README.md` will link to

- [ ] **Step 1: Create capstone directory and placeholder README**

```bash
mkdir -p course/capstone
```

Write `course/capstone/README.md` with content that:
- Tells the learner what the capstone is (integrate all 7 Parts into a complete 本地论文研究助手)
- Shows the learning path from Part 1 through Capstone as a simple list
- Makes clear this is a placeholder — the full capstone comes in Phase R8
- Mentions: agent receives research questions, retrieves from local paper fixtures, extracts evidence, generates cited reports, uses memory, delegates to child agents, has a Workbench UI, and leaves inspectable event trails — all offline

See the spec Appendix for the exact capstone deliverables structure that this placeholder should preview.

- [ ] **Step 2: Commit**

```bash
git add course/capstone/README.md
git commit -m "feat: add capstone placeholder for course teaching redesign"
git push origin HEAD
```

---

### Task 2: Replace Chapter Template

**Files:**
- Modify: `docs/course/chapter-template.md`

**Interfaces:**
- Consumes: teaching principles from spec
- Produces: new chapter template that all subsequent Part rewrites follow

- [ ] **Step 1: Replace template content**

Overwrite `docs/course/chapter-template.md` with the new template from the spec Appendix. Key changes from the old template:

1. **New section structure**: Part → Section types ([FULL] vs [LIGHT] cycle intensity)
2. **New callout format**: `[DD]`, `[TRAP]`, `[CHECK]`, `[BIG]`, `[DEEP]` as primary ASCII tags
3. **New exercise feedback requirements**: every L1/L2/L3 must include Common Errors, Failure Output Interpretation, Where To Go Back, Why Correct Answer Is Correct
4. **New ASCII diagram format**: Architecture Map, Object Relationship Diagram, Event Flow Timeline, Data Flow Diagram
5. **New narrative elements**: Part opener connects to 本地论文研究助手, Part closer teases next Part

The exact template content is in `docs/specs/2026-06-30-course-teaching-redesign.md` Appendix section.

- [ ] **Step 2: Verify template completeness**

Check that the new template specifies:
- [x] Learner Contract format
- [x] Section types and their cycle intensity ([FULL] vs [LIGHT])
- [x] Callout format with ASCII tags as primary
- [x] Exercise feedback requirements (4 items per exercise)
- [x] ASCII diagram format
- [x] Eval Gate format with specific pytest/ruff commands
- [x] Checkpoint format (L3 Design + Reflection + Discussion)
- [x] Part opener/closer with narrative transition

- [ ] **Step 3: Commit**

```bash
git add docs/course/chapter-template.md
git commit -m "feat: replace chapter template with project-driven Part format"
git push origin HEAD
```

---

### Task 3: Update Course Roadmap

**Files:**
- Modify: `docs/course/roadmap.md`

**Interfaces:**
- Consumes: new Part structure from spec
- Produces: updated roadmap that `course/README.md` references

- [ ] **Step 1: Update Course Promise**

Change the opening paragraph to: "The course should teach Agent engineering through a single, growing project: a 本地论文研究助手 (local paper research assistant). Every Part adds a capability to this assistant. All examples run offline with FakeModel and static paper fixtures. The event trail is the primary learning tool — learners inspect it, break it, and fix it."

- [ ] **Step 2: Restructure Beginner Track as Part-based path**

Replace the numbered Beginner Track with a table showing:
- Step number
- File to read/do
- What capability the assistant gains

Make it clear that Parts 1-7 build on each other, ending with Capstone.

- [ ] **Step 3: Update Shape section**

Replace the 24-week domain list with:
```
1. Part 1: Agent Kernel — the smallest think-act-observe loop, with event trail
2. Part 2: Research Core — source → evidence → claim → report evidence chain
3. Part 3: Memory and Skills — persistent memory policies and skill loading
4. Part 4: Multi-Agent Delegation — child context isolation and budget accounting
5. Part 5: Workbench Product — product adapter, FastAPI API, React workbench
6. Part 6: Framework Comparisons — method for comparing frameworks on the same task
7. Part 7: Production Readiness — diagnostics, persistence, approval, and sandbox policies
8. Capstone — integrate all Parts into a complete 本地论文研究助手
```

- [ ] **Step 4: Update Chapter Contract → Part Contract**

Replace with new Part Contract that matches the new template requirements (at least 1 full Build→Inspect→Break→Fix→Reflect cycle, 3-tier exercises with feedback, 2+ ASCII diagrams, 3+ callouts, eval gate, reflection questions).

- [ ] **Step 5: Update Current Materials and Near-Term Course Work**

Add capstone and spec entries. Replace Near-Term with R1-R9 phases.

- [ ] **Step 6: Commit**

```bash
git add docs/course/roadmap.md
git commit -m "feat: update course roadmap for Part structure and project-driven approach"
git push origin HEAD
```

---

### Task 4: Rewrite Chapter 00 — Part 1 Section 1 (Mental Model + Narrative)

**Files:**
- Modify: `course/chapters/00-before-agent-kernel.md`

**Interfaces:**
- Consumes: new chapter template, narrative from spec
- Produces: Part 1 Section 1 — first contact with narrative, mental model, architecture map

**Target structure after rewrite:**

```
# Part 1: 你的第一个 Agent — 让它跑起来，并且能看懂它做了什么

## 你的本地论文研究助手现在需要：会跑
[Narrative intro: you're building an assistant for a research team.
 Today it does nothing. Part 1 makes it run and makes it observable.]

## Section 1: Agent 的心智模型 — 它到底在管什么

### Problem Hook
[Without Agent runtime, you'd do everything manually. Show the pain.]

### Explore
[Walk through a real scenario: researcher asks question → you search papers → 
 you summarize. What pieces do you need to automate this?]

### 概念：人话版
[Agent = 记账员 (bookkeeper), not a brain.
 Table: 7 roles with human-meaning + code-name.
 Introduce concepts one at a time as the story needs them, not all 9 at once.]

> [BIG] 大局观：Architecture Map (ASCII) — Part 1 in the full system

> [DD] 设计决策：Why AgentMessage ≠ provider message

> [DD] 设计决策：Why FakeModel for learning (not a real model)

> [CHECK] 检查一下：Model vs AgentRuntime vs ToolRuntime — whose job is what?

## The First Rule Of This Course
[保留但加强：不要只看 final answer。看 event sequence。
 连接回"本地论文研究助手"叙事：研究者需要可信的答案，不是漂亮但找不到出处的话。]

## 继续 Section 2 之前
[前置要求 + 三段自查问题 + 指向 ch01]
```

**Key transformations from old content:**
1. Title changes from "Chapter 00: Before You Build An Agent Kernel" to "Part 1: 你的第一个 Agent"
2. Old "The Plain Version" → new "Problem Hook" + "Explore" (active, scenario-driven)
3. Old mental model table → kept but introduced AFTER the scenario, not before
4. Old "Why Not Use A Real Model First" → upgraded to `[DD]` callout with explicit alternatives
5. Old "First Rule" → kept with stronger narrative connection
6. Old "Checkpoint" (4 recall questions) → moved to end-of-Section-1 gate, 3 concept-check questions
7. NEW: `[BIG]` Architecture Map (ASCII) showing Part 1 position
8. NEW: `[DD]` callout for AgentMessage vs provider message
9. NEW: Transition to Section 2 (in ch01)

- [ ] **Step 1: Rewrite the opening through Goal**

Write the new title and narrative opener. Replace everything from the current `# Chapter 00` through `## Goal` with the Part 1 opener that introduces the 本地论文研究助手 narrative and sets expectations.

- [ ] **Step 2: Write Section 1 content**

Write Problem Hook, Explore, and 概念 sections following the target structure. The concept table should introduce objects as the story needs them. Add all `[BIG]`, `[DD]`, and `[CHECK]` callouts.

- [ ] **Step 3: Add Architecture Map (ASCII)**

Draw an ASCII diagram showing: User Input → AgentRunner (containing ContextBuilder, Model, ToolRuntime) → RunEvent stream → Final Answer. Keep it simple enough to memorize.

- [ ] **Step 4: Rewrite closing sections**

Update "The First Rule Of This Course" and "继续 Section 2 之前" sections. The pre-Section-2 gate should have 3 checkpoint questions testing concept understanding, not recall.

- [ ] **Step 5: Verify quality gates for this file**

Check:
- [x] Narrative "本地论文研究助手" introduced in opening
- [x] At least 1 ASCII diagram (Architecture Map)
- [x] At least 2 `[DD]` callouts
- [x] At least 1 `[CHECK]` callout
- [x] At least 1 `[BIG]` callout
- [x] Clear transition to Section 2 (ch01)

- [ ] **Step 6: Commit**

```bash
git add course/chapters/00-before-agent-kernel.md
git commit -m "feat: rewrite ch00 as Part 1 Section 1 with narrative and mental model"
git push origin HEAD
```

---

### Task 5: Rewrite Chapter 01 — Part 1 Sections 2-5 (Build, Break, Fix, Gate)

**Files:**
- Modify: `course/chapters/01-agent-kernel-foundations.md`

**Interfaces:**
- Consumes: Task 4 output (Section 1 narrative and mental model), new template
- Produces: Part 1 Sections 2-5 — Build [FULL], Break & Fix [FULL], Product [LIGHT], Eval Gate [LIGHT], Checkpoint

**Target structure after rewrite:**

```
# Part 1: Agent Kernel Foundations (Sections 2-5)
> 接 Section 1。如果你还没读 00-before-agent-kernel.md，先回去读完。

## Section 2: 第一个可观察的 Agent Loop [BUILD — FULL CYCLE]

### 概念：最小的 think-act-observe loop
[Introduce the loop with a concrete event sequence example.
 NOT a list of 9 objects. Show the events first, then explain what
 each event means.]

### Build: 你的第一个 Agent Run
> L1 Follow 练习
[Code: plain final response first (simplest case), then tool call.
 Learner types the code, observes event_type_sequence.]

#### 🔍 练习反馈
[Common Errors × 3, Failure Output Interpretation, Where To Go Back]

### Inspect The Trail
[events_to_records, inspect tool_call and tool_result records]

> [DD] 设计决策：Why custom JSON tool-call format instead of OpenAI function calling

### Modify: 改 echo 的返回值
> L2 Modify 练习
[Change echo handler return value. Predict: does event_type_sequence change? does final_message change?]

#### 🔍 练习反馈
[排查步骤, Why Correct Answer Is Correct]

> [TRAP] 常见陷阱：tool result ≠ model response. Tool returns data, model interprets it.
>        They are separate events for a reason.

---

## Section 3: Break It, Fix It — 失败也是信息 [BREAK & FIX — FULL CYCLE]

### Break It: 故意调一个不存在的工具
[Change "echo" to "missing" in tool call JSON. Run. Catch UnknownToolError.
 Observe error event in the trail.]

### Fix It: 分析事件轨迹
[Don't change code. Answer 3 diagnostic questions about the event sequence.
 This trains the "read the trail, don't just fix and move on" habit.]

> [DD] 设计决策：Why AgentRunner doesn't pre-validate tool existence before calling

#### 🔍 练习反馈
[Common Errors, Failure Output, Where To Go Back]

---

## Section 4: 接入你的 Workbench [PRODUCT — LIGHT]

[Map each event type to its future Workbench UI location.
 Timeline panel, Tool Inspector, Failure Diagnostics.
 Emphasize: Part 1 code defines protocols the product will depend on.]

> [BIG] 大局观：Part 1 event trail → Part 5 Workbench timeline data source

---

## Section 5: Eval Gate [GATE — LIGHT]

[Minimal eval: pytest + ruff commands.
 Core self-check: write a complete tool run from scratch in Python shell.]

---

## Checkpoint

### L3 Design 练习
[Design a multi-tool calculator agent. 4 tools (add, subtract, multiply, divide).
 Two consecutive tool calls. Write FakeModel sequence, ToolDefinitions, 
 predict event_type_sequence, run, compare.]

#### 🔍 练习反馈
[Common design errors, self-check criteria]

### Reflection
[3 design-decision questions, not recall]

### Discussion
[2 open questions for self-study or team discussion]

---

**完成 Part 1 后，你的本地论文研究助手现在可以：接收研究问题，调用工具，返回答案，
并且整个运行过程被 event trail 完整记录。**

**Next — Part 2 teaser: 你的助手能回答了，但它的回答有证据吗？**
```

**Key transformations from old content:**
1. Old "Core Objects" table (9 objects upfront) → removed. Objects introduced as needed in Build section.
2. Old "Minimal Example" → restructured as L1 Follow with feedback loop
3. Old "Failure Lab Preview" → upgraded to full Break & Fix section with diagnostic questions
4. Old "Product Integration" → kept as Product Section, added `[BIG]` callout
5. Old "Eval Gate" → kept, simplified
6. Old "Checkpoint" (5 recall questions) → replaced with L3 Design + Reflection + Discussion
7. NEW: L2 Modify exercise (change echo return, predict impact)
8. NEW: `[DD]` callouts × 2 (tool-call JSON format, pre-validation vs fail-and-record)
9. NEW: `[TRAP]` callout (tool result vs model response)
10. NEW: Exercise feedback subsections (🔍 练习反馈) for every L1/L2/L3
11. NEW: Part closer with narrative summary + Part 2 teaser

- [ ] **Step 1: Write Section 2 — Build [FULL CYCLE]**

Write the concept intro (think-act-observe loop as event sequence), the L1 Follow Build exercise (plain response + tool call), the Inspect The Trail subsection, the L2 Modify exercise, and all callouts and feedback sections.

- [ ] **Step 2: Write Section 3 — Break & Fix [FULL CYCLE]**

Write the Break It subsection (missing tool), the Fix It diagnostic questions, and the `[DD]` callout about pre-validation.

- [ ] **Step 3: Write Sections 4 & 5 — Product + Gate [LIGHT]**

Write the Product Section (event-to-UI mapping table) and Eval Gate (pytest/ruff commands + core self-check).

- [ ] **Step 4: Write Checkpoint — L3 Design + Reflection + Discussion**

Write the multi-tool calculator L3 Design exercise with feedback, 3 reflection questions, 2 discussion questions, and the Part closer with Part 2 teaser.

- [ ] **Step 5: Verify combined Part 1 (ch00 + ch01) meets all quality gates**

Combined checklist:
- [x] Narrative "本地论文研究助手" established and referenced throughout
- [x] At least 2 ASCII diagrams (Architecture Map + event flow)
- [x] At least 3 `[DD]` callouts (AgentMessage, FakeModel, tool-call JSON, pre-validation)
- [x] At least 2 `[TRAP]` callouts (tool result vs model response, FakeModel JSON format)
- [x] At least 2 `[CHECK]` callouts
- [x] At least 2 `[BIG]` callouts (architecture, product integration)
- [x] L1 Follow exercise × 2 (plain response + tool call) with feedback
- [x] L2 Modify exercise × 1 with feedback
- [x] L3 Design exercise × 1 with feedback
- [x] Break & Fix section with complete cycle
- [x] Product integration section
- [x] Eval gate with specific commands
- [x] Reflection questions (design decisions, not recall)
- [x] Discussion questions
- [x] Part 2 teaser

- [ ] **Step 6: Commit**

```bash
git add course/chapters/01-agent-kernel-foundations.md
git commit -m "feat: rewrite ch01 as Part 1 Sections 2-5 with three-tier exercises"
git push origin HEAD
```

---

### Task 6: Rewrite Lab 01 — Three-Tier Exercises + Feedback Loop

**Files:**
- Modify: `course/labs/01-agent-runner-lab.md`

**Interfaces:**
- Consumes: Task 5 (Part 1 chapter content with exercise structure)
- Produces: standalone lab file with self-contained setup and all four exercises

**Target structure:**
```
# Lab 01: Build And Inspect An Agent Run

## Goal
[Three-tier table: L1 Follow (Ex 1,2) / L2 Modify (Ex 3) / L3 Design (Ex 4)]

## Setup
[PYTHONPATH shell + imports]

## Exercise 1 (L1 Follow): Plain Final Response
[Code + expected output + self-check + 🔍 练习反馈]

## Exercise 2 (L1 Follow): Add An Echo Tool
[Code + expected output + self-check + 🔍 练习反馈]

## Exercise 3 (L2 Modify): Inspect And Modify The Trajectory
[events_to_records + immutability demo + 🔍 练习反馈 + [TRAP] callout]

## Exercise 4 (L3 Design): Design A Multi-Tool Calculator
[Requirements only, no skeleton + 🔍 练习反馈]
```

**Key changes from old lab:**
1. Old Ex 3 (inspect trajectory) + Old Ex 4 (break tool name) → merged into new chapter Sections 2-3
2. Old Ex 3 immutability demo → kept as L2 Modify with prediction element
3. Old Ex 4 → removed from lab (moved to chapter Break & Fix section)
4. NEW: Ex 4 L3 Design (multi-tool calculator from scratch)
5. NEW: Every exercise has 🔍 练习反馈 section
6. NEW: Exercise tier labels (L1/L2/L3)
7. NEW: `[TRAP]` callout in Ex 3

- [ ] **Step 1: Rewrite opening and Setup**

Add tier table and self-contained setup instructions. Keep imports identical to old version (no code API changes).

- [ ] **Step 2: Rewrite Exercise 1 (L1 Follow) with feedback**

Keep existing code. Add 🔍 练习反馈 with: Common Errors (wrong import, wrong FakeModelResponse param), Failure Output Interpretation (empty event list fix), Where To Go Back.

- [ ] **Step 3: Rewrite Exercise 2 (L1 Follow) with feedback**

Keep existing code. Add 🔍 练习反馈 with: Common Errors (JSON format, missing tools param, wrong FakeModel response order), Failure Output Interpretation (only 2 events = JSON not parsed), Where To Go Back.

- [ ] **Step 4: Rewrite Exercise 3 as L2 Modify (immutability)**

Keep existing events_to_records + immutability demo code. Add prediction step before running. Add 🔍 练习反馈 and `[TRAP]` about records[].payload vs .payload syntax.

- [ ] **Step 5: Write Exercise 4 as L3 Design (multi-tool calculator)**

Write the requirements: 4 tools (add/subtract/multiply/divide), task is "3+4 then ×2", learner writes FakeModel sequence, ToolDefinitions, predicts event_type_sequence, runs, compares. Add 🔍 练习反馈 with common design errors and self-check event sequence.

- [ ] **Step 6: Commit**

```bash
git add course/labs/01-agent-runner-lab.md
git commit -m "feat: rewrite lab01 with three-tier exercises and feedback loops"
git push origin HEAD
```

---

### Task 7: Rewrite Solution 01 — Add Design Rationale

**Files:**
- Modify: `course/solutions/01-agent-runner-solution.md`

**Interfaces:**
- Consumes: Task 6 (lab exercises)
- Produces: solution file with design rationale and "why correct" explanations

**Key changes from old solution:**
1. Old "What this proves" (bullets) → upgraded to "What This Proves" + "Why This Design" (structured sections)
2. Every design rationale connects back to the 论文研究助手 narrative
3. Old "Final Takeaway" → strengthened with narrative connection + Part 2 teaser

- [ ] **Step 1: Add narrative-connected opening**

Write new intro explaining how to use the solution (先看 What This Proves → 再看代码 → 最后看 Why This Design). Add the imports block (unchanged).

- [ ] **Step 2: Upgrade Exercise 1-4 solutions**

For each exercise:
- Keep the code block (unchanged)
- Replace "What this proves" bullets with structured "What This Proves" (what the assertions validate) + "Why This Design" (what design decision this validates, why it matters for the 论文研究助手)

Specific design rationale to include:
- Ex 1: ContextBuilder auto-inserts system prompt → ensures the "cite evidence" rule is always at the top
- Ex 2: Tool result appended before second model_request → model has full context for its final answer
- Ex 3: `events_to_records` returns independent copy → Workbench UI can safely filter/sort/display without data corruption
- Ex 4: `UnknownToolError` carries `.events` → failed runs are inspectable; most important engineering habit in the course

- [ ] **Step 3: Rewrite Final Takeaway**

Strengthen with narrative connection: "看 event sequence 不看 final answer" → why this matters for Part 2 (evidence chain), Part 5 (timeline UI), Part 7 (production diagnostics).

- [ ] **Step 4: Commit**

```bash
git add course/solutions/01-agent-runner-solution.md
git commit -m "feat: rewrite solution01 with design rationale and narrative connection"
git push origin HEAD
```

---

### Task 8: Rewrite Course README — Project-Driven Learning Guide

**Files:**
- Modify: `course/README.md`

**Interfaces:**
- Consumes: all previous task outputs (new chapter/lab/solution/capstone content)
- Produces: rewritten learner entrypoint that explains the project-driven approach

**Key changes from old README:**
1. Title → "本地论文研究助手 — 从零构建一个可观察的 Agent 系统"
2. Opening → project narrative (build a real assistant, not learn abstract concepts)
3. Who This Is For → add "want a complete, demonstrable project"
4. Beginner Track → Part-based table (step → file → assistant capability gained)
5. How To Study → replaces "How To Study One Chapter"; adds 10-step Part workflow
6. Common Stuck Points → add L3-specific issues
7. Course Map → reorganized as Part 1 / Parts 2-7 / Capstone / Framework reports

- [ ] **Step 1: Rewrite opening and Who This Is For**

Replace title and intro paragraphs. Add project narrative emphasis.

- [ ] **Step 2: Rewrite Beginner Track as Part-based table**

Replace numbered list with a table: Step | Content | 你的助手获得的能力. Make it visual.

- [ ] **Step 3: Rewrite How To Study**

Replace "How To Study One Chapter" with "How To Study One Part" — 10-step workflow matching the Build→Inspect→Break→Fix→Reflect cycle.

- [ ] **Step 4: Update Common Stuck Points and Course Map**

Add L3-specific stuck points. Reorganize Course Map by Part.

- [ ] **Step 5: Commit**

```bash
git add course/README.md
git commit -m "feat: rewrite course README as project-driven learning guide"
git push origin HEAD
```

---

### Task 9: Update Docs Index and Progress Tracking

**Files:**
- Modify: `docs/README.md`
- Create: `docs/progress/phases/phase-r1.md`
- Modify: `docs/progress/overall.md`

- [ ] **Step 1: Update docs/README.md**

Add to Document Index:
- `specs/2026-06-30-course-teaching-redesign.md`
- `plans/2026-06-30-phase-r1-course-teaching-redesign.md`

Update Course Index Part 1 entries to reflect new narrative framing.

- [ ] **Step 2: Create progress file**

Write `docs/progress/phases/phase-r1.md` with: Status, Start date, Branch, Goal, Task checklist (10 items), Exit Signal checklist.

- [ ] **Step 3: Update overall progress dashboard**

Add Phase R1 row to the phase index table in `docs/progress/overall.md`.

- [ ] **Step 4: Commit**

```bash
git add docs/README.md docs/progress/phases/phase-r1.md docs/progress/overall.md
git commit -m "feat: update docs index and progress tracking for Phase R1"
git push origin HEAD
```

---

### Task 10: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest -q
```
Expected: all tests pass (199 passed baseline). No runtime code was changed.

- [ ] **Step 2: Run ruff**

```bash
uv run ruff check .
```
Expected: clean.

- [ ] **Step 3: Verify internal links**

Check that all referenced files in `course/README.md` exist:
- `reference/python-terminal-primer.md`
- `reference/agent-kernel-glossary.md`
- `chapters/00-before-agent-kernel.md`
- `chapters/01-agent-kernel-foundations.md`
- `labs/00-environment-check.md`
- `labs/01-agent-runner-lab.md`
- `solutions/01-agent-runner-solution.md`
- `capstone/README.md`

- [ ] **Step 4: Run docs freshness check**

```bash
uv run pytest tests/course/test_docs_freshness.py -q
```

- [ ] **Step 5: Quality gate checklist**

Verify Part 1 (ch00 + ch01 combined) meets all 8 quality gates from spec:

| Gate | Requirement | Evidence to collect before marking pass |
|------|------------|--------|
| Teaching flow | At least 1 full Build→Inspect→Break→Fix→Reflect cycle | Read ch00/ch01 and cite the sections that implement Build, Inspect, Break, Fix, and Reflect. |
| Exercise | L1×2, L2×1, L3×1; each with full feedback | Count exercises and confirm each has Common Errors, Failure Output Interpretation, Where To Go Back, and Why Correct Answer Is Correct. |
| Narrative | 本地论文研究助手贯穿 Part 1 | Check ch00/ch01/lab/solution/README for the same project thread. |
| Visual | 2+ ASCII diagrams | Record diagram section names. |
| Sidebar | 3+ [DD]/[TRAP] callouts | Count `[DD]` and `[TRAP]` markers. |
| Docs sync | README, roadmap, index, progress updated | Check touched docs and progress files. |
| Test | pytest + ruff pass | Paste fresh command results into the final progress note. |
| Offline | All examples use FakeModel | Search for real API/provider references in rewritten Part 1 files. |

- [ ] **Step 6: Final commit if any verification fixes needed**

```bash
git add -A
git commit -m "chore: final verification fixes for Phase R1"
git push origin HEAD
```

---

## Dependency Order

```
Task 1 (capstone placeholder) ──┐
Task 2 (chapter template)   ──┼──► Task 4 (ch00) ──► Task 5 (ch01) ──► Task 6 (lab01) ──► Task 7 (solution01)
Task 3 (roadmap)            ──┘                                                                          │
                                                                                                         ▼
                                                                                              Task 8 (course README)
                                                                                                         │
                                                                                                         ▼
                                                                                              Task 9 (docs index + progress)
                                                                                                         │
                                                                                                         ▼
                                                                                              Task 10 (verification)
```

Tasks 1-3 can run in parallel. Tasks 4-7 are sequential (each builds on the prior). Task 8 depends on 4-7. Task 9 depends on all. Task 10 is final verification.

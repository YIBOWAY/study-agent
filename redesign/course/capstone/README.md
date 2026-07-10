# Capstone: 本地论文研究助手

> **Status:** Phase R8 complete — this is the real Capstone brief, not a placeholder.
>
> Build one offline research assistant that composes Parts 1-7. Do the starter first; open the solution only after your tests and rubric self-check.

## Product Brief

You are shipping a **local paper research assistant** for a small research team.

The researcher asks:

> "Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate when producing a cited report?"

Your assistant must answer **offline**:

1. Load local paper fixtures (no network).
2. Retrieve relevant sources.
3. Extract evidence quotes.
4. Produce a cited report where every claim traces to evidence.
5. Write at least one memory under an explicit write policy.
6. Load at least one skill package.
7. Optionally delegate a focused review child task.
8. Build a Workbench snapshot with an inspectable timeline.
9. Record diagnostics / JSONL persistence / approval+sandbox decisions as production trust evidence.

This is not a chat demo. The deliverable is an inspectable research run.

## Learner Contract

- **Who this is for**: learners who finished Parts 1-7 (Beginner Track or Engineer Track).
- **Before you start**: complete Part 2 evidence chain, Part 3 memory/skills, Part 5 workbench snapshot, and Part 7 production contracts.
- **You will build**: one integrated offline Capstone agent under `course/capstone/starter/` (or your own module that satisfies the same rubric).
- **You will prove it**: rubric Pass on all six criteria + Capstone tests green.
- **Offline guarantee**: static `paper_fixtures/`, `FakeModel`, `FakeRetriever`, no API keys.

## What You Already Have From Parts 1-7

```text
Part 1  AgentRunner + FakeModel + event trail
Part 2  Source -> Evidence -> Claim -> Report -> ClaimSourceLink
Part 3  MemoryEngine policies + SkillRuntime progressive disclosure
Part 4  DelegationRuntime, budgets, child isolation, filter_tools_for_role
Part 5  WorkbenchSnapshot + to_record() product shape
Part 6  Build-vs-adopt comparison method (use as a reflection lens)
Part 7  RunDiagnostics, JsonlRunEventStore, ApprovalPolicy, SandboxPolicy
```

## Directory Map

```text
course/capstone/
|-- README.md                 # this brief
|-- rubric.md                 # six success criteria
|-- paper_fixtures/
|   |-- papers.json           # offline papers
|   `-- README.md
|-- skills/
|   `-- citation-check/       # Capstone skill package
|-- starter/
|   |-- agent_starter.py      # TODO skeleton
|   `-- test_starter.py       # scaffold tests
`-- solution/
    |-- agent.py              # reference implementation
    |-- test_run.py           # rubric-backed tests
    |-- trajectory.jsonl      # sample event log
    |-- report.md             # sample research report
    `-- reflection.md         # design-decision reflection
```

## Required Workflow

### Step 1 — Read the brief and rubric

1. Skim this README.
2. Read [rubric.md](rubric.md).
3. Inspect [paper_fixtures/papers.json](paper_fixtures/papers.json).

### Step 2 — Fill the starter

From `redesign/`:

```bash
# study the skeleton
sed -n '1,220p' course/capstone/starter/agent_starter.py

# run starter tests (they skip until you implement TODOs)
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/starter/test_starter.py -q
```

Implement in `starter/agent_starter.py`:

1. Load paper fixtures → ingest sources.
2. Retrieve with `FakeRetriever`.
3. Build evidence + claims + report + claim-source links.
4. Write memory with `MemoryWritePolicy`.
5. Load the Capstone citation-check skill.
6. Run a scripted `AgentRunner` tool trail (search tool is enough).
7. Build `WorkbenchSnapshot` with timeline items from run events.
8. Produce diagnostics, JSONL store records, and policy decisions.

### Step 3 — Self-grade with the rubric

Use [rubric.md](rubric.md). Every criterion needs evidence, not vibes.

### Step 4 — Compare with the solution (after your attempt)

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py -q
PYTHONPATH=packages/research_core/src uv run python course/capstone/solution/agent.py
```

Then read:

- [solution/report.md](solution/report.md)
- [solution/reflection.md](solution/reflection.md)
- [solution/trajectory.jsonl](solution/trajectory.jsonl)

## Architecture Target

```text
Research question
      |
      v
paper_fixtures -> SourceIngestor -> FakeRetriever
      |
      +--> Evidence / Claim / Report / ClaimSourceLink
      |
      +--> MemoryEngine (write policy + recall)
      |
      +--> SkillRuntime (citation-check package)
      |
      +--> AgentRunner tool trail (FakeModel)
      |         optional: DelegationRuntime child review
      |
      +--> WorkbenchSnapshot.to_record()
      |
      v
RunDiagnostics + JsonlRunEventStore + Approval/Sandbox decisions
```

## Honesty Notes (do not fake these)

> [TRAP] **Skill/memory role fields are not auto-enforced**
>
> `AgentRolePolicy.skill_names` and `memory_kinds` are declarative labels unless your child factory wires `SkillRuntime` / `MemoryEngine`. Tool allowlists should use `filter_tools_for_role(...)`.

> [TRAP] **MEMORY_*/SKILL_* events are not automatic**
>
> Writing memory or loading a skill does not invent runtime events by itself. Capstone can still *use* memory and skills without claiming those event types fired.

> [TRAP] **max_runtime_seconds is inspectable, not auto-killed**
>
> Use `SandboxPolicy.runtime_decision(elapsed_seconds)`. `AgentRunner` does not start a wall-clock timer for you.

> [DD] **Why Capstone stays on handwritten research_core contracts**
>
> **Chose**: compose Parts 1-7 public APIs offline.
> **Did not choose**: pull LangChain/CrewAI into Capstone for a prettier demo.
> **Because**: the course goal is inspectable contracts and event trails, not framework tourism. Part 6 already taught how to compare frameworks later.

## Success Criteria (summary)

1. Evidence from >=3 local sources.
2. Every claim traces to evidence.
3. >=1 skill loaded and >=1 memory write policy used.
4. Workbench snapshot timeline is inspectable.
5. Capstone tests pass offline.
6. Reflection explains 3 design decisions.

Details and scoring: [rubric.md](rubric.md).

## Eval Gate

From `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/solution/test_run.py -q
PYTHONPATH=packages/research_core/src uv run pytest course/capstone/starter/test_starter.py -q
PYTHONPATH=packages/research_core/src uv run pytest -q
PYTHONPATH=packages/research_core/src uv run ruff check .
```

## Suggested Timebox

| Track | Time |
| --- | --- |
| Engineer Track | 3-5 hours |
| Beginner Track | 6-10 hours across two sessions |

If stuck, re-open the Part that owns the missing piece (Part 2 for links, Part 3 for memory/skills, Part 5 for snapshot integrity, Part 7 for diagnostics/policy).

## After Capstone

- Re-read Part 6: would you still keep handwritten contracts for this assistant?
- Optional R9 materials (patterns, troubleshooting, design-decision index) are planned support docs, not required for Capstone Pass.

---

**完成 Capstone 后，你应该能演示一个完整、离线、可复盘的本地论文研究助手。**

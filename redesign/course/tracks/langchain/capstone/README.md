# Capstone（LangChain 轨）: 本地论文研究助手

> Build one offline LC research assistant that composes Parts 1–7. Do the starter first; open the solution only after your tests and rubric self-check.

## Product Brief

Researcher question:

> "Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate when producing a cited report?"

Your assistant must answer **offline for unit tests**:

1. Load local paper fixtures.
2. Retrieve with `KeywordRetriever`.
3. Extract evidence quotes.
4. Produce a cited report where every claim traces to evidence.
5. Write at least one memory under an explicit write policy.
6. Load at least one skill package.
7. Optionally delegate a focused review child task.
8. Build a Workbench snapshot with an inspectable timeline.
9. Record diagnostics / JSONL steps / approval+sandbox decisions as production trust evidence.

This track uses `langchain_course` only—**never import** `research_core`.

## Learner Contract

- **Before you start**: finish LC Parts 1–7 materials (F0–F3).
- **You will build**: starter under `starter/` (or equivalent) satisfying the rubric.
- **You prove it**: six rubric criteria Pass + solution/starter tests green.
- **Offline unit guarantee**: fixtures + scripted steps; live DeepSeek is optional polish, not the gate.

## Directory Map

```text
course/tracks/langchain/capstone/
|-- README.md
|-- rubric.md
|-- paper_fixtures/
|-- skills/citation-check/
|-- starter/
|   |-- agent_starter.py
|   `-- test_starter.py
`-- solution/
    |-- agent.py
    |-- test_run.py
    |-- trajectory.jsonl
    |-- report.md
    `-- reflection.md
```

## Commands

From `redesign/`:

```bash
uv sync --group langchain-course

# starter (skips until TODOs filled)
uv run pytest course/tracks/langchain/capstone/starter -q

# reference solution
uv run pytest course/tracks/langchain/capstone/solution -q

# full LC package units
uv run pytest packages/langchain_course/tests -q
```

## Mapping to Parts 1–7

| Part | LC building blocks used here |
| --- | --- |
| 1 | `AgentStep` trail (scripted) |
| 2 | `PaperDoc`, `KeywordRetriever`, `EvidenceItem`, `ClaimItem`, `build_claim_links` |
| 3 | `Notebook` + `SkillLoader` |
| 4 | optional `DelegationCoordinator` |
| 5 | `WorkbenchSnapshot` |
| 6 | reflection lens (build vs adopt) |
| 7 | `RunDiagnostics`, `JsonlStepStore`, `ApprovalPolicy`, `SandboxPolicy` |

# Capstone（LangChain 轨）: 本地论文研究助手

> Build one offline LC research assistant that composes Parts 1–7. Do the starter first; open the solution only after your tests and rubric self-check.

## Product Brief

Researcher question:

> "Does citation grounding matter for trustworthy RAG evaluation, and what should a local research assistant remember or delegate when producing a cited report?"

Your assistant must answer **offline for unit tests**:

1. Load local paper fixtures.
2. Retrieve through `LangChainPaperRetriever(BaseRetriever)` and `Document`.
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
- **You prove it**: six outcome criteria plus the LC-execution gate Pass, and
  solution/starter tests stay green.
- **Offline unit guarantee**: deterministic `BaseChatModel` + local fixtures; the
  real message/tool/callback path still runs, while live DeepSeek stays optional.

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
| 1 | real `run_tool_calling_agent` + deterministic `BaseChatModel` + `BaseTool` |
| 2 | `PaperDoc` → `Document` → `LangChainPaperRetriever` + evidence links |
| 3 | `Notebook` + `SkillLoader` |
| 4 | `DelegationCoordinator`; child also runs the LC loop |
| 5 | `WorkbenchSnapshot` |
| 6 | reflection lens (build vs adopt) |
| 7 | `RunDiagnostics`, `JsonlStepStore`, `ApprovalPolicy`, `SandboxPolicy` |

## Build → Inspect → Break → Fix

1. **Build:** run the solution and inspect `result.steps`.
2. **Inspect:** find `model_response`, `tool_call`, `tool_decision`, `tool_result`,
   `delegate_start`, and `delegate_finish`.
3. **Break:** change the approval rule from `keyword_*` to `other_*`; verify the
   tool is blocked before retrieval.
4. **Fix:** restore the allow rule and keep the tool-decision record.
5. **Reflect:** explain which objects come from LangChain and which invariants
   remain course-owned.

## Optional live boundary

```bash
RUN_DEEPSEEK_TESTS=1 uv run pytest \
  course/tracks/langchain/capstone/solution -m integration -q
```

The live smoke asks DeepSeek to call the same local retrieval tool. It asserts
structure and non-empty final text, never exact model prose.

## Exit questions

1. Why is a deterministic `BaseChatModel` a real offline framework test while a
   manually assembled `AgentStep` list is not?
2. What happens before `BaseTool.invoke`, and what evidence remains afterward?
3. Which Capstone component would LangGraph replace or deepen in F4/F5?

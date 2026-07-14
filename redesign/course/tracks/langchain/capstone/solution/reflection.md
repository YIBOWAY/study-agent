# Capstone Reflection (LangChain track)

## Decision 0 — deterministic BaseChatModel, not synthetic steps

- **Chose:** scripted outputs inside a real `BaseChatModel`, followed by
  `run_tool_calling_agent` and `BaseTool.invoke`.
- **Rejected:** manually creating the main `model_request/tool_call/tool_result`
  trail.
- **Because:** offline should remove network nondeterminism without bypassing
  the LangChain execution behavior being taught.

## Decision 1 — deterministic LC execution vs live DeepSeek for the gate

- **Chose:** Offline deterministic `BaseChatModel` through the real LC loop.
- **Rejected:** Requiring `RUN_DEEPSEEK_TESTS=1` for Capstone Pass.
- **Because:** Live API is non-deterministic and costs money; the Capstone must prove composition and contracts offline. Live smoke remains optional polish.

## Decision 2 — Independent snapshot types vs importing research_core.product

- **Chose:** `langchain_course.workbench.WorkbenchSnapshot` with matching nine-panel *shape*.
- **Rejected:** Importing handwritten product types into the LC track.
- **Because:** Parallel-track design forbids bidirectional imports; semantic对照 is enough for teaching.

## Decision 3 — Post-hoc delegation budget remains honest

- **Chose:** Keep LC `DelegationCoordinator` post-hoc budget counting (same F2 honesty).
- **Rejected:** Pretending the coordinator can interrupt a child model before every
  request merely because the child uses a deterministic LC model.
- **Because:** The coordinator receives the child result after its runner returns,
  then accounts for `model_request` steps. The main tool loop has a real pre-tool
  approval hook; delegation model budgets remain post-hoc and are labeled honestly.

## Optional note after Part 6

After running LC Parts 1–7, inspectability-heavy tasks still often favor handwritten profiles, while state-resume-heavy tasks favor LangGraph records. Capstone staying offline does not mean LC is “worse”—it means the exam weights decide the winner.

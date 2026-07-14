# Capstone Reflection (LangChain track)

## Decision 1 — Scripted steps vs live DeepSeek for the Capstone gate

- **Chose:** Offline scripted `AgentStep` trail for unit tests.
- **Rejected:** Requiring `RUN_DEEPSEEK_TESTS=1` for Capstone Pass.
- **Because:** Live API is non-deterministic and costs money; the Capstone must prove composition and contracts offline. Live smoke remains optional polish.

## Decision 2 — Independent snapshot types vs importing research_core.product

- **Chose:** `langchain_course.workbench.WorkbenchSnapshot` with matching nine-panel *shape*.
- **Rejected:** Importing handwritten product types into the LC track.
- **Because:** Parallel-track design forbids bidirectional imports; semantic对照 is enough for teaching.

## Decision 3 — Post-hoc delegation budget remains honest

- **Chose:** Keep LC `DelegationCoordinator` post-hoc budget counting (same F2 honesty).
- **Rejected:** Pretending Capstone enforces hard pre-flight step interruption for scripted runners.
- **Because:** Learners should not relearn a fantasy contract in Capstone; document the boundary and show parent `delegate_*` trail instead.

## Optional note after Part 6

After running LC Parts 1–7, inspectability-heavy tasks still often favor handwritten profiles, while state-resume-heavy tasks favor LangGraph records. Capstone staying offline does not mean LC is “worse”—it means the exam weights decide the winner.

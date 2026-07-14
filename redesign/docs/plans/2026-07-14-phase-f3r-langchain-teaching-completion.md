# Phase F3R: LangChain Teaching Completion — Implementation Plan

**Goal:** Turn the structurally complete F0–F3 LangChain track into a genuinely
framework-native, executable, beginner-ready course before LangGraph F4 starts.

**Why this phase exists:** The F0–F3 audit found that all expected files and
offline unit tests existed, but Parts 2–3 and 7 mostly reimplemented handwritten
contracts, the Capstone used scripted `AgentStep` records instead of running the
LangChain agent loop, Parts 5–7 were thinner than the course teaching contract,
and the LangChain Markdown files were absent from the executable-docs gate.

**Primary source baseline:** LangChain Core 1.x `Document`, `BaseRetriever`,
`RunnableSequence`, `RunnableParallel`, `RunnableWithMessageHistory`, callback
handlers, `BaseTool`, and message/tool-calling contracts. The track stays free of
LangGraph and does not import `research_core`.

## Completion Contract

F3R is complete only when all of the following are true:

1. Part 2 uses LangChain `Document`, `BaseRetriever`, and a composed Runnable.
2. Part 3 demonstrates `RunnableWithMessageHistory` while preserving explicit
   write/recall policy as a separate product decision.
3. Part 4 demonstrates real `RunnableParallel` composition in addition to the
   budgeted sequential coordinator.
4. Part 6 derives its LC baseline by running `run_tool_calling_agent`, not by
   constructing a synthetic trail.
5. Part 7 records real LangChain callback activity and enforces approval before
   a tool executes.
6. The offline Capstone invokes the real LC tool loop with a deterministic chat
   model; an optional DeepSeek smoke verifies the live boundary.
7. Every Part has a problem hook, handwritten mapping, Build -> Inspect -> Break
   -> Fix -> Reflect cycle, L1/L2/L3 lab, detailed feedback, runnable solution,
   eval gate, and forward connection.
8. LangChain chapters/labs/solutions are covered by the Markdown Python-block
   gate; explicitly live blocks are excluded by fence language, not by accident.
9. Track links, plan/progress/index status, dependency policy, and completion
   language agree everywhere.

## Tasks

- [x] Task 1: Add failing tests for LC-native Part 2/3/4 contracts.
- [x] Task 2: Implement Document/Retriever/Runnable, history, and parallel workers.
- [x] Task 3: Add failing tests for callbacks, pre-tool approval, real baseline,
  and real-loop Capstone.
- [x] Task 4: Implement Part 6/7 and Capstone runtime corrections.
- [x] Task 5: Rewrite and deepen Parts 0–7 + Capstone teaching materials.
- [x] Task 6: Expand executable-docs and synchronization gates.
- [x] Task 7: Sync README/course/docs/progress/spec surfaces.
- [x] Task 8: Run full verification and close F3R.

## Verification

```bash
uv sync --group langchain-course
uv run pytest packages/langchain_course/tests -q
uv run pytest course/tracks/langchain/capstone/solution -q
uv run pytest -q
uv run pytest tests/course/test_markdown_python_blocks.py -q
uv run pytest tests/course/test_docs_freshness.py -q
uv run ruff check .
git diff --check
```

Live verification remains opt-in:

```bash
RUN_DEEPSEEK_TESTS=1 uv run pytest \
  packages/langchain_course/tests \
  course/tracks/langchain/capstone/solution -m integration -q
```

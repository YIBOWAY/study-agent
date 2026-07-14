# Phase F3R Progress: LangChain Teaching Completion

Status: Complete

Started: 2026-07-14
Completed: 2026-07-14
Branch: `codex/redesign-course-r7`

## Goal

Close the gap between “all files exist” and “the learner genuinely studies and
builds with LangChain”: framework-native primitives, real agent-loop Capstone,
full teaching cycles, executable docs, and synchronized course truth.

## Checklist

- [x] LC-native Parts 2–4
- [x] Callbacks + pre-tool approval in Part 7
- [x] Real-loop Part 6 baseline and Capstone
- [x] Parts 0–7 + Capstone teaching rewrite
- [x] LC Markdown gate
- [x] Index/progress/spec synchronization
- [x] Full verification

## Audit Baseline

- Existing package tests: 58 passed, 1 skipped.
- Existing LC Capstone tests: 2 passed.
- Existing main suite: 215 passed.
- Existing LC Markdown was not in the official gate.
- F3R plan: `docs/plans/2026-07-14-phase-f3r-langchain-teaching-completion.md`.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-07-14 | Audit accepted; F3R started with completion contract and tests-first workflow. |
| 2026-07-14 | Added `Document`/`BaseRetriever`/LCEL, message history, `RunnableParallel`, callbacks, pre-tool approval, deterministic real-loop model, and optional live Capstone path. |
| 2026-07-14 | Deepened Parts 0–7 and Capstone with Build/Inspect/Break/Fix, L1–L3 practice, feedback, checkpoints, troubleshooting, and official API boundary references. |
| 2026-07-14 | Added all 23 LangChain chapter/lab/solution files to the executable Markdown gate; synchronized indexes, dependency ranges, and `uv.lock`. |

## Final Verification

| Command | Result |
| --- | --- |
| `uv run pytest packages/langchain_course/tests -q` | 65 passed, 1 skipped (optional live test) |
| `uv run pytest course/tracks/langchain/capstone/solution -q` | 2 passed, 1 skipped (optional live test) |
| `uv run pytest -q` | 217 passed; 2 intentional `RunnableWithMessageHistory` migration warnings |
| `uv run pytest tests/course/test_markdown_python_blocks.py -q` | 6 passed; LC gate covers 23 teaching files |
| `uv run pytest tests/course/test_docs_freshness.py -q` | 4 passed |
| `uv run ruff check .` | passed |
| `uv lock --check` | passed; 52 packages resolved |
| `git diff --check` | passed |

The two deprecation warnings are an explicit lesson boundary, not an ignored
failure: LangChain 1.4.9 still executes `RunnableWithMessageHistory`, while the
warning points learners forward to LangGraph persistence in F4.

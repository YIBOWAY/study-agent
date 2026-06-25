# Phase 1 Progress: Agent Kernel Course Spine

Status: In progress

Started: 2026-06-25
Completed: Not completed
Branch: `codex/redesign-phase-1`

## Goal

Build the first executable agent kernel spine: tool runtime, context builder, agent runner, trajectory regression tests, and the first course chapter/lab.

## Planned Deliverables

- Phase 1 executable plan under `redesign/docs/plans/`.
- `ToolCall`, `ToolResult`, `ToolDefinition`, and `ToolRuntime`.
- `ContextBuilder` for deterministic internal message assembly.
- `AgentRunner` for a minimal think-act-observe loop using `FakeModel`.
- Trajectory recording helpers and regression tests.
- Course chapter and lab for Agent Kernel Foundations.
- Architecture docs updated with the Phase 1 runtime flow.

## Progress Log

| Date | Update |
| --- | --- |
| 2026-06-25 | Phase 1 started after Phase 0 branch push. Progress dashboard created before kernel implementation. |
| 2026-06-25 | Tool Runtime delivered in `d390cd2`: immutable tool calls/results/definitions, duplicate registration checks, invocation path, JSON-compatible validation, and runtime exports. Verification: `15 passed` for tool tests, full redesign suite `48 passed`, scoped `ruff` clean. |
| 2026-06-25 | Context Builder delivered in `624c71e`: deterministic system prompt insertion, caller system-message rejection, latest-message windowing, runtime exports, and AgentMessage role normalization hardening. Verification: context/message tests `18 passed`, full redesign suite `59 passed`, scoped `ruff` clean. |
| 2026-06-25 | AgentRunner delivered and review-hardened: deterministic model/tool loop, final assistant responses, model/tool events, max-step budget, malformed JSON tool-call handling, unknown-tool separation, and error-event attachment for model/tool failures. Verification: runner/tools tests `31 passed`, full redesign suite `75 passed`, `ruff check .` clean. |

## Delivered Files

- `packages/research_core/src/research_core/runtime/tools.py`
- `packages/research_core/src/research_core/runtime/context.py`
- `packages/research_core/src/research_core/runtime/messages.py`
- `packages/research_core/src/research_core/runtime/runner.py`
- `tests/research_core/test_tools.py`
- `tests/research_core/test_context.py`
- `tests/research_core/test_messages.py`
- `tests/research_core/test_runner.py`

## Current Focus

Next implementation slice: trajectory regression helpers for stable event records and exact event type sequence assertions.

## Verification Target

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

Phase 1 is complete only when those commands pass and this progress file records the delivered files and verification result.

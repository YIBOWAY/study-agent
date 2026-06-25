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

## Verification Target

Run from `redesign/`:

```bash
uv run pytest -q
uv run ruff check .
```

Phase 1 is complete only when those commands pass and this progress file records the delivered files and verification result.

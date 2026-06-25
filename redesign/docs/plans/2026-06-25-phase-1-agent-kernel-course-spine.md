# Agent Kernel Course Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first executable agent kernel spine: tool runtime, context builder, minimal agent runner, trajectory regression tests, and the first course chapter/lab.

**Architecture:** Phase 1 extends `packages/research_core` without importing FastAPI, React, provider SDKs, databases, or legacy root code. Runtime contracts remain Pydantic-free dataclasses and deterministic offline tests use `FakeModel`. The agent runner uses internal `AgentMessage` and append-only `RunEvent` records as its observable protocol.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, dataclasses, protocols, JSON fixtures.

---

## File Structure

Create or update these files:

- Create: `redesign/packages/research_core/src/research_core/runtime/tools.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/context.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/runner.py`
- Create: `redesign/packages/research_core/src/research_core/runtime/trajectory.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/tests/research_core/test_tools.py`
- Create: `redesign/tests/research_core/test_context.py`
- Create: `redesign/tests/research_core/test_runner.py`
- Create: `redesign/tests/research_core/test_trajectory.py`
- Create: `redesign/course/chapters/01-agent-kernel-foundations.md`
- Create: `redesign/course/labs/01-agent-runner-lab.md`
- Create: `redesign/course/solutions/01-agent-runner-solution.md`
- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-1.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

Do not modify legacy `app/`, `frontend/`, root `tests/`, root `eval/`, or root project configuration.

## Contracts

### Tool Runtime

- `ToolCall`: immutable call request with `id`, `name`, and JSON-compatible `arguments`.
- `ToolResult`: immutable tool output with `call_id`, `name`, `content`, and JSON-compatible `metadata`.
- `ToolDefinition`: immutable tool registration with `name`, `description`, and `handler`.
- `ToolRuntime`: registry that rejects duplicate tools, invokes tools by name, records successful output, and converts exceptions into `ToolResult` when configured by the runner.

Tool handlers take `Mapping[str, Any]` and return `Mapping[str, Any]`. Handler output must be strict JSON-compatible through `freeze_json_value`.

### Context Builder

- `ContextBuilder.build(system_prompt, messages)` returns internal `AgentMessage` objects.
- A non-empty system prompt is inserted as the first message.
- Existing system messages in `messages` are rejected to keep the system boundary explicit.
- `max_messages` keeps the last N non-system messages while preserving the system prompt.

### Agent Runner

The minimal runner supports:

- deterministic `run_id`;
- max step budget;
- model request/response events;
- JSON tool-call responses from the model;
- tool call/result events;
- final assistant response when the model returns plain text.

Tool-call response format:

```json
{
  "tool_call": {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"}
  }
}
```

### Trajectory Regression

Trajectory helpers convert `RunEvent` objects into stable plain records and assert exact event type sequences. These helpers are test-only friendly but live in runtime because later labs and evals reuse them.

## Task 1: Add Progress Dashboard and Phase 1 Plan

**Files:**

- Create: `redesign/docs/progress/README.md`
- Create: `redesign/docs/progress/overall.md`
- Create: `redesign/docs/progress/phases/phase-0.md`
- Create: `redesign/docs/progress/phases/phase-1.md`
- Create: `redesign/docs/progress/phases/phase-2.md`
- Create: `redesign/docs/progress/phases/phase-3.md`
- Create: `redesign/docs/progress/phases/phase-4.md`
- Create: `redesign/docs/progress/phases/phase-5.md`
- Create: `redesign/docs/progress/phases/phase-6.md`
- Create: `redesign/docs/progress/phases/phase-7.md`
- Create: `redesign/docs/plans/2026-06-25-phase-1-agent-kernel-course-spine.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [x] **Step 1: Add progress dashboard files**

Create the progress files with Phase 0 marked complete, Phase 1 marked in progress, and Phases 2-7 marked pending.

- [x] **Step 2: Add this Phase 1 plan**

Save this plan at `redesign/docs/plans/2026-06-25-phase-1-agent-kernel-course-spine.md`.

- [x] **Step 3: Verify docs are indexed**

Run:

```bash
rg -n "progress|phase-1-agent-kernel" redesign/docs/README.md redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md redesign/docs/progress
```

Expected: the progress folder and Phase 1 plan are discoverable from the docs index and roadmap.

## Task 2: Add Tool Runtime

**Files:**

- Create: `redesign/packages/research_core/src/research_core/runtime/tools.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/tests/research_core/test_tools.py`

- [x] **Step 1: Write failing tests**

Create `redesign/tests/research_core/test_tools.py` with tests for:

- `ToolCall` rejects blank `id` and `name`.
- `ToolCall.arguments` is copied and recursively read-only.
- `ToolResult.to_message()` returns an `AgentMessage` with role `MessageRole.TOOL`.
- `ToolRuntime.register()` rejects duplicate names.
- `ToolRuntime.invoke()` calls the handler and returns a `ToolResult`.
- `ToolRuntime.invoke()` raises `KeyError` for unknown tools.
- Non-JSON-compatible arguments or result payloads are rejected with `ValueError`.

Use this representative assertion:

```python
def test_tool_runtime_invokes_registered_tool() -> None:
    runtime = ToolRuntime()
    runtime.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = runtime.invoke(ToolCall(id="call_1", name="echo", arguments={"text": "hello"}))

    assert result.call_id == "call_1"
    assert result.name == "echo"
    assert result.content == {"text": "hello"}
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_tools.py -q
```

Expected: failure because `research_core.runtime.tools` does not exist.

- [x] **Step 3: Implement tool runtime**

Create `tools.py` with `ToolCall`, `ToolResult`, `ToolDefinition`, and `ToolRuntime`. Reuse `freeze_json_value` and `thaw_json_value` for JSON-compatible argument/result contracts.

- [x] **Step 4: Export tool runtime contracts**

Update `runtime/__init__.py` to export `ToolCall`, `ToolDefinition`, `ToolResult`, and `ToolRuntime`.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_tools.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/tools.py tests/research_core/test_tools.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 3: Add Context Builder

**Files:**

- Create: `redesign/packages/research_core/src/research_core/runtime/context.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/tests/research_core/test_context.py`

- [x] **Step 1: Write failing tests**

Create tests for:

- non-empty system prompt is inserted as first message;
- blank system prompt is rejected;
- caller-provided system messages are rejected;
- `max_messages` keeps the latest non-system messages;
- returned list is independent from caller list mutation.

Representative assertion:

```python
def test_context_builder_inserts_system_prompt() -> None:
    builder = ContextBuilder()
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    context = builder.build(system_prompt="You are careful.", messages=messages)

    assert [message.role for message in context] == [MessageRole.SYSTEM, MessageRole.USER]
    assert context[0].content == "You are careful."
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_context.py -q
```

Expected: failure because `research_core.runtime.context` does not exist.

- [x] **Step 3: Implement context builder**

Create `ContextBuilder` as a small class with `__init__(max_messages: int | None = None)` and `build(system_prompt: str, messages: Sequence[AgentMessage]) -> list[AgentMessage]`.

- [x] **Step 4: Export context builder**

Update `runtime/__init__.py` to export `ContextBuilder`.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_context.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/context.py tests/research_core/test_context.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 4: Add Agent Runner

**Files:**

- Create: `redesign/packages/research_core/src/research_core/runtime/runner.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/tests/research_core/test_runner.py`

- [x] **Step 1: Write failing tests**

Create tests for:

- plain model response becomes final assistant message;
- JSON tool-call response invokes `ToolRuntime` and loops back to the model;
- runner emits `model_request`, `model_response`, `tool_call`, and `tool_result` events;
- max step exhaustion raises `RuntimeError`;
- malformed tool-call JSON raises `ValueError` and emits an `error` event before raising.

Representative tool loop test:

```python
def test_agent_runner_executes_tool_call_then_returns_final_answer() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}'
            ),
            FakeModelResponse(content="final answer"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = AgentRunner(model=model, tools=tools).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.final_message.content == "final answer"
    assert [event.type.value for event in result.events] == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_runner.py -q
```

Expected: failure because `research_core.runtime.runner` does not exist.

- [x] **Step 3: Implement runner**

Create:

- `AgentRunResult(final_message, messages, events)`.
- `AgentRunner(model, tools=None, context_builder=None, max_steps=4)`.
- `run(run_id, system_prompt, user_message)`.

Use deterministic message IDs and event IDs based on counters inside one run.

- [x] **Step 4: Export runner**

Update `runtime/__init__.py` to export `AgentRunner` and `AgentRunResult`.

- [x] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_runner.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/runner.py tests/research_core/test_runner.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 5: Add Trajectory Regression Helpers

**Files:**

- Create: `redesign/packages/research_core/src/research_core/runtime/trajectory.py`
- Modify: `redesign/packages/research_core/src/research_core/runtime/__init__.py`
- Create: `redesign/tests/research_core/test_trajectory.py`

- [ ] **Step 1: Write failing tests**

Create tests for:

- `events_to_records(events)` returns stable `RunEvent.to_record()` lists;
- `event_type_sequence(events)` returns a list of event type strings;
- mutating returned records does not mutate source events.

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_trajectory.py -q
```

Expected: failure because `research_core.runtime.trajectory` does not exist.

- [ ] **Step 3: Implement helpers**

Create `events_to_records(events: Sequence[RunEvent]) -> list[dict[str, Any]]` and `event_type_sequence(events: Sequence[RunEvent]) -> list[str]`.

- [ ] **Step 4: Export helpers**

Update `runtime/__init__.py` to export both functions.

- [ ] **Step 5: Verify**

Run:

```bash
cd redesign && uv run pytest tests/research_core/test_trajectory.py -q
cd redesign && uv run ruff check packages/research_core/src/research_core/runtime/trajectory.py tests/research_core/test_trajectory.py
```

Expected: tests pass and ruff reports `All checks passed!`.

## Task 6: Add Course Chapter, Lab, and Solution

**Files:**

- Create: `redesign/course/chapters/01-agent-kernel-foundations.md`
- Create: `redesign/course/labs/01-agent-runner-lab.md`
- Create: `redesign/course/solutions/01-agent-runner-solution.md`

- [ ] **Step 1: Add chapter**

Write a chapter that explains internal messages, events, tools, context, and the runner loop. Include one short code example that uses `FakeModel`, `ToolRuntime`, and `AgentRunner`.

- [ ] **Step 2: Add lab**

Write a lab with these exercises:

- run a plain model response;
- add an `echo` tool;
- inspect the trajectory event sequence;
- break the tool name and observe the error path.

- [ ] **Step 3: Add solution**

Write the expected solution using the public Phase 1 contracts.

- [ ] **Step 4: Verify doc references**

Run:

```bash
rg -n "AgentRunner|ToolRuntime|ContextBuilder|event_type_sequence" redesign/course redesign/docs
```

Expected: chapter, lab, and solution reference the public Phase 1 contracts.

## Task 7: Update Architecture, Glossary, Roadmap, and Progress

**Files:**

- Modify: `redesign/docs/architecture/runtime.md`
- Modify: `redesign/docs/glossary.md`
- Modify: `redesign/docs/README.md`
- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-1.md`
- Modify: `redesign/docs/plans/2026-06-25-redesign-execution-roadmap.md`

- [ ] **Step 1: Update runtime architecture**

Add a Phase 1 section describing the loop:

```text
ContextBuilder -> model_request -> model_response -> optional tool_call/tool_result -> final assistant message.
```

- [ ] **Step 2: Update glossary**

Add `ToolRuntime`, `ContextBuilder`, `AgentRunner`, and `Trajectory Regression`.

- [ ] **Step 3: Update progress**

Mark Phase 1 delivered files, verification result, and commit hash after commit.

- [ ] **Step 4: Verify docs**

Run:

```bash
rg -n "AgentRunner|ToolRuntime|ContextBuilder|Trajectory Regression|Phase 1" redesign/docs
```

Expected: architecture, glossary, progress, and roadmap mention Phase 1 contracts.

## Task 8: Final Phase 1 Verification

**Files:**

- Modify: `redesign/docs/progress/overall.md`
- Modify: `redesign/docs/progress/phases/phase-1.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
cd redesign && uv run pytest -q
cd redesign && uv run ruff check .
git diff --check
```

Expected:

```text
All tests pass.
All checks passed!
No whitespace errors.
```

- [ ] **Step 2: Clean generated side effects**

Remove generated `redesign/.venv`, `redesign/.ruff_cache`, `redesign/.pytest_cache`, `redesign/uv.lock`, and any `__pycache__` directories unless an approved plan adds them as tracked artifacts.

- [ ] **Step 3: Commit and push**

Commit with a message that records the Phase 1 deliverables and verification commands. Push branch `codex/redesign-phase-1`.

## Phase 1 Completion Checklist

- [x] `ToolRuntime` tests pass.
- [x] `ContextBuilder` tests pass.
- [x] `AgentRunner` tests pass.
- [ ] trajectory regression helper tests pass.
- [ ] Course chapter, lab, and solution exist.
- [x] `redesign/docs/progress/overall.md` and `phase-1.md` are updated.
- [ ] `cd redesign && uv run pytest -q` passes.
- [ ] `cd redesign && uv run ruff check .` passes.
- [ ] No legacy `app/`, `frontend/`, root `tests/`, or root `eval/` files are modified.

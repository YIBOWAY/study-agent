# Lab 01: Build and Inspect an Agent Run

This lab uses only Phase 1 public contracts. Run commands from `redesign/`.

## Setup

Open a Python shell with the project package path:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

Use these imports:

```python
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
    events_to_records,
)
from research_core.testing import FakeModel, FakeModelResponse
```

## Exercise 1: Plain Final Response

Create a `FakeModel` with one `FakeModelResponse(content="final answer")`.

Run `AgentRunner(model=model).run(...)` with:

- `run_id="lab_plain"`
- `system_prompt="You are careful."`
- `user_message="hello"`

Inspect:

- `result.final_message.content`
- `event_type_sequence(result.events)`
- `events_to_records(result.events)`

Expected event sequence:

```python
["model_request", "model_response"]
```

## Exercise 2: Add an Echo Tool

Create a `ToolRuntime`, register an `echo` tool, and script the model with two
responses:

1. A JSON tool call to `echo`.
2. A plain final answer.

Use this tool handler:

```python
lambda arguments: {"text": arguments["text"]}
```

Expected event sequence:

```python
[
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
```

Inspect the `tool_result` record and confirm it includes `content` and
`metadata`.

## Exercise 3: Inspect the Trajectory

Use `events_to_records(result.events)` and compare the third and fourth records:

- The third record should be a `tool_call`.
- The fourth record should be a `tool_result`.

Mutate the returned records locally and confirm the original `RunEvent.payload`
objects remain unchanged.

## Exercise 4: Break the Tool Name

Change the model's tool call from `"name": "echo"` to `"name": "missing"`.

Wrap the run in `try` / `except KeyError as exc`.

Inspect `exc.events` and verify:

```python
["model_request", "model_response", "tool_call", "error"]
```

The final error event should have:

```python
{"kind": "unknown_tool"}
```

This is the first rule of debuggable agent systems: failed runs still produce a
trajectory.

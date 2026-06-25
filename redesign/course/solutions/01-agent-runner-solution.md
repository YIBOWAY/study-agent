# Solution 01: Agent Runner Lab

Run these snippets from a Python shell started in `redesign/`:

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Exercise 1

```python
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
    events_to_records,
)
from research_core.testing import FakeModel, FakeModelResponse

model = FakeModel([FakeModelResponse(content="final answer")])
result = AgentRunner(model=model).run(
    run_id="lab_plain",
    system_prompt="You are careful.",
    user_message="hello",
)

assert result.final_message.content == "final answer"
assert event_type_sequence(result.events) == ["model_request", "model_response"]
assert events_to_records(result.events)[0]["payload"]["message_ids"] == [
    "system_1",
    "user_1",
]
```

## Exercise 2

```python
model = FakeModel(
    [
        FakeModelResponse(
            content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}'
        ),
        FakeModelResponse(content="The tool said hello."),
    ]
)

tools = ToolRuntime()
tools.register(
    ToolDefinition(
        name="echo",
        description="Return the input text.",
        handler=lambda arguments: {"text": arguments["text"]},
    )
)

result = AgentRunner(model=model, tools=tools).run(
    run_id="lab_tool",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

assert result.final_message.content == "The tool said hello."
assert event_type_sequence(result.events) == [
    "model_request",
    "model_response",
    "tool_call",
    "tool_result",
    "model_request",
    "model_response",
]
```

## Exercise 3

```python
records = events_to_records(result.events)

assert records[2]["type"] == "tool_call"
assert records[2]["payload"]["tool_call"] == {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"},
}

assert records[3]["type"] == "tool_result"
assert records[3]["payload"]["tool_result"] == {
    "call_id": "call_1",
    "name": "echo",
    "content": {"text": "hello"},
    "metadata": {},
}

records[3]["payload"]["tool_result"]["content"]["text"] = "mutated"
assert result.events[3].payload["tool_result"]["content"]["text"] == "hello"
```

## Exercise 4

```python
model = FakeModel(
    [
        FakeModelResponse(
            content='{"tool_call": {"id": "call_1", "name": "missing", "arguments": {"text": "hello"}}}'
        )
    ]
)

try:
    AgentRunner(model=model, tools=tools).run(
        run_id="lab_missing_tool",
        system_prompt="You are careful.",
        user_message="Say hello through a missing tool.",
    )
except KeyError as exc:
    error_events = exc.events
else:
    raise AssertionError("Expected missing tool to raise KeyError")

assert event_type_sequence(error_events) == [
    "model_request",
    "model_response",
    "tool_call",
    "error",
]
assert error_events[-1].payload["error"]["kind"] == "unknown_tool"
```

The final snippet is the behavior to remember: a failed agent run is still a
structured runtime artifact.

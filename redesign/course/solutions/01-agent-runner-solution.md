# Solution 01: Agent Runner Lab

这份 solution 用来对答案。建议你先自己完成 lab，再看这里。

所有 snippets 都从 `redesign/` 的 Python shell 运行：

```bash
PYTHONPATH=packages/research_core/src uv run python
```

## Imports

```python
from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    UnknownToolError,
    event_type_sequence,
    events_to_records,
)
from research_core.testing import FakeModel, FakeModelResponse
```

## Exercise 1 Solution

```python
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

What this proves:

- `ContextBuilder` inserted `system_1`.
- The user message became `user_1`.
- A plain model response ends the run immediately.

## Exercise 2 Solution

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

What this proves:

- JSON model output was parsed as a `ToolCall`.
- `ToolRuntime` found and executed the registered `echo` tool.
- The tool result was appended before the second model request.
- The second model response became the final answer.

## Exercise 3 Solution

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

What this proves:

- The event trail contains enough detail to debug the tool step.
- `events_to_records` returns plain records for inspection.
- Mutating those records does not mutate the original `RunEvent` payload.

## Exercise 4 Solution

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
except UnknownToolError as exc:
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

What this proves:

- Missing tools are not ignored.
- The runner emits an `error` event before raising.
- The exception carries `exc.events`, so failed runs are still inspectable.

## Final Takeaway

The most important lesson is not “how to write an echo tool”.

The important lesson is:

```text
An agent runtime should make its path visible.
```

When the run succeeds, inspect the event sequence. When the run fails, inspect the event sequence. That habit is what turns Agent work from prompt guessing into engineering.

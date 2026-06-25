# Chapter 01: Agent Kernel Foundations

Phase 1 turns the redesign runtime contracts into the smallest useful agent
kernel. The kernel is intentionally offline-first: it uses internal messages,
append-only events, a deterministic fake model, and in-process tools before any
provider SDK, database, UI, or framework is introduced.

## Theory

The first kernel lesson is about separating the agent mechanism from provider
payloads and product UI. A useful agent runtime needs stable internal messages,
observable events, explicit context ownership, deterministic tools, and failure
paths that can be inspected after the run.

## Handwritten Implementation

The Phase 1 implementation is the smallest useful version of that kernel.

`AgentMessage` is the internal conversation unit. It is not an OpenAI,
Anthropic, or LangChain message. Keeping this format internal gives the runtime
one stable shape for tests, labs, replay, adapters, and future UI timelines.

`RunEvent` is the observable trace of a run. The runner appends events for model
requests, model responses, tool calls, tool results, and errors. Later phases
will store, display, replay, and compare these events, so Phase 1 treats event
order as part of the contract.

`ToolRuntime` is the local tool registry. Tools are registered as
`ToolDefinition` objects and invoked through `ToolCall` objects. Results come
back as `ToolResult` objects, preserving JSON-compatible content and metadata.

`ContextBuilder` owns the system boundary. It inserts one system prompt at the
front of each model request and rejects caller-provided system messages, so
application code cannot smuggle competing instructions into the context.

`AgentRunner` is the minimal think-act-observe loop. It sends a context to the
model, records the response, parses JSON tool calls, invokes tools, appends tool
messages, and loops until the model returns plain text or the max-step budget is
exhausted.

## Response Shape

Plain model text is a final answer. JSON model responses are reserved for tool
calls and must use this shape:

```json
{
  "tool_call": {
    "id": "call_1",
    "name": "echo",
    "arguments": {"text": "hello"}
  }
}
```

Malformed tool-call JSON, unknown tools, tool failures, bad model responses, and
budget exhaustion all emit an `error` event before raising. That makes failed
runs inspectable instead of disappearing into exceptions.

## Product Integration

The Workbench will eventually render `RunEvent` records as the run timeline.
Phase 1 does not build the product UI, but it creates the protocol that later
screens depend on:

- `model_request` and `model_response` feed the run timeline,
- `tool_call` and `tool_result` feed tool inspection,
- `error` events feed failure diagnostics,
- trajectory helpers provide regression fixtures for product smoke checks.

## Failure Lab

The lab deliberately breaks a tool name and asks the learner to inspect
`exc.events`. A failed agent run should still leave a structured runtime
artifact, which is the first debugging rule for the project.

## Framework Comparison

Frameworks are intentionally deferred for this chapter. The comparison task is
now defined: rebuild the same echo-tool run in `course/framework_comparisons/`
and compare event visibility, test setup, and failure diagnostics against the
handwritten `AgentRunner`.

## Eval Gate

The chapter gate is the trajectory sequence for the tool run:

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

The project-level verification command is:

```bash
uv run pytest -q
uv run ruff check .
```

## Minimal Example

```python
from research_core.runtime import AgentRunner, ToolDefinition, ToolRuntime
from research_core.testing import FakeModel, FakeModelResponse

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
    run_id="run_1",
    system_prompt="You are careful.",
    user_message="Say hello through the tool.",
)

print(result.final_message.content)
```

The important output is not just the final message. The event stream should be:

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

That sequence is the first trajectory regression surface in the redesign.

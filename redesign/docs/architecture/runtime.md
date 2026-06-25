# Runtime Architecture

## AgentMessage

`AgentMessage` is the internal message format. It is not an OpenAI, Anthropic, or framework-specific message.

## RunEvent

`RunEvent` records what happened during a research or agent run. Event logs are append-only and provide the basis for timeline UI, replay, trajectory tests, and evals.

## Event Stream

The event stream is the append-only runtime protocol built from `RunEvent`
records. Phase 1 makes event ordering part of the executable contract for the
agent kernel.

## Phase 1 Agent Kernel

The Phase 1 loop is:

```text
ContextBuilder -> model_request -> model_response -> optional tool_call/tool_result -> final assistant message
```

`ContextBuilder` inserts the reserved system prompt and rejects caller-provided
system messages. `AgentRunner` then sends the built context to the model and
records `model_request` and `model_response` events. If the model response is a
JSON `tool_call`, the runner invokes `ToolRuntime`, records `tool_call` and
`tool_result`, appends the tool message, and loops back to the model. If the
model response is plain text, the runner returns that assistant message as the
final answer.

Failures are observable. Malformed tool calls, unknown tools, model failures,
tool failures, invalid model responses, and max-step exhaustion all append an
`error` event before raising. The raised exception carries the partial event
trajectory as `exc.events`.

Trajectory helpers provide the first regression surface:

- `event_type_sequence(events)` returns stable event type strings.
- `events_to_records(events)` returns independent plain event records.

## Provider Boundary

Provider adapters convert internal messages into provider-specific request
payloads and normalize provider responses back into internal runtime records.
The Phase 0 fake model provider uses the same internal contracts as live
model providers.

## Phase 0 Runtime Scope

Phase 0 defines the contracts only:

- message roles,
- immutable agent messages,
- event types,
- immutable run events,
- deterministic fake model responses.

## Phase 1 Runtime Scope

Phase 1 adds the first executable kernel:

- `ToolCall`, `ToolResult`, `ToolDefinition`, and `ToolRuntime`,
- `ContextBuilder`,
- `AgentRunner` and `AgentRunResult`,
- trajectory regression helpers,
- the first course chapter, lab, and solution.

## Fake Provider Boundary

`FakeModel` is part of the testing surface. It records calls and returns scripted responses so labs, trajectory tests, and product smoke checks can run without API keys.

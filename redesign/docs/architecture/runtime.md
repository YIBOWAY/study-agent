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

## Research Data Boundary

Phase 2 adds `research_core.research` as the first domain layer above the runtime
contracts. It defines `Project`, `ResearchRun`, `Source`, `Evidence`, `Claim`,
and `Report`, plus deterministic `SourceIngestor`, `FakeRetriever`, and
claim-source mapping helpers.

The runtime package remains independent from the research package. Research
contracts may reuse runtime immutability helpers, but `research_core.runtime`
must not import research entities.

## Phase 3 Memory and Skills Boundary

Phase 3 adds two stateful-agent surfaces above the runtime kernel:

- `research_core.memory`: deterministic in-process memory records, write
  policies, recall policies, and token recall.
- `research_core.skills`: folder-based skill loading with progressive
  disclosure.

Memory and skills remain offline-first. Memory is not persistent storage or
embedding search yet. Skills load `SKILL.md` first and only read files under
`references/` when `SkillRuntime.read_reference()` is called explicitly.

The event enum now includes the comprehensive stream values needed by later
phases: `skill_step`, `delegate_event`, `compaction_start`,
`compaction_finish`, and `eval_result`.

## Phase 4 Delegation Boundary

Phase 4 adds `research_core.delegation` as the first multi-agent layer above the
single-agent kernel. The runtime is deterministic and sequential in this phase;
true async execution, cancellation propagation, remote transport, and product UI
surfaces are deferred.

The Phase 4 delegation loop is:

```text
DelegationTask -> DelegationRuntime -> child runner -> DelegationResult -> DelegationMergeResult
```

`AgentRolePolicy` owns the child system prompt and scoped tool, skill, and
memory names. `DelegationTask` owns the parent run ID, child run ID, objective,
role policy, and explicit child context messages. System messages are rejected
from child context; the role policy is the only child system prompt source.

`DelegationRuntime.run_task()` emits parent events:

- `delegate_start`: task/run IDs, role ID, scoped tools/skills/memory, and budget.
- `delegate_event`: one wrapper around each child `RunEvent.to_record()`.
- `delegate_finish`: status, step count, final child message or error.

Child events keep the child run ID and are embedded in parent events as records
instead of being merged into parent messages. This keeps child context isolated
and makes the parent timeline replayable.

Budget accounting is local and deterministic:

- `max_child_runs` rejects too many child tasks before running.
- `max_steps_per_child` rejects over-scoped roles before running and marks a
  child result failed if observed child events exceed the allowed step count.
- `max_total_steps` prevents launching a child when the remaining budget cannot
  cover that task's allowed steps.

`A2AAdapterStub` exports a versioned task-delegation record for future remote
agent work. It deliberately omits parent-private task metadata, carries only
context message IDs, and raises `NotImplementedError` on send attempts.

## Phase 5 Product Boundary

Phase 5 does not change the runtime loop. Instead, it adapts runtime and domain
records into `research_core.product.WorkbenchSnapshot` so product surfaces can
inspect a run without depending on raw internals.

The Phase 5 product flow is:

```text
RunEvent / research / memory / skills / delegation records
  -> WorkbenchSnapshot.to_record()
  -> research_api FastAPI endpoints
  -> apps/web React panels
```

The API and web layers read product records. They do not own runtime state,
provider calls, memory policy, skill loading, or delegation execution.

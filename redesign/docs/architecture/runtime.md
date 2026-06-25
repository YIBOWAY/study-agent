# Runtime Architecture

## AgentMessage

`AgentMessage` is the internal message format. It is not an OpenAI, Anthropic, or framework-specific message.

## RunEvent

`RunEvent` records what happened during a research or agent run. Event logs are append-only and provide the basis for timeline UI, replay, trajectory tests, and evals.

## Event Stream

The event stream is the append-only runtime protocol built from `RunEvent`
records. Phase 0 defines the primitive event contract only; ordering rules,
replay semantics, storage, and UI timeline behavior are introduced by Phase 1+
approved plans.

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

## Fake Provider Boundary

`FakeModel` is part of the testing surface. It records calls and returns scripted responses so labs, trajectory tests, and product smoke checks can run without API keys.

# Phase 7 Evaluation, Safety, and Observability Design

## Goal

Add the engineering controls that turn the learning Agent platform into a measurable and safer system:

- preflight hardening for Phase 6 MCP behavior
- RAG and Agent evaluation
- prompt-injection and tool-call guardrails
- local tracing and cost accounting backed by SQLite

No LangSmith, Langfuse, RAGAS, NeMo Guardrails, or new SaaS dependency is added.

## Preflight Hardening

MCP and rerank are hardened before Phase 7 features:

- MCP server tool failures return protocol-level `isError=True`.
- External MCP tool calls use the same timeout policy as local tools.
- Windows MCP command parsing preserves backslash paths.
- MCP debug invocation is routed through guardrails when enabled.
- `mcp` is pinned to the verified version.
- Rerank supports fail-soft fallback for transient or permission errors.

## Evaluation

`evaluation_service.py` is extended with three LLM-as-judge helpers:

- faithfulness
- context precision
- answer relevance

Each helper asks a caller-provided `judge_fn` for strict JSON and returns safe fallback scores on parse failure.

`agent_evaluator.py` adds a small batch evaluator that records completion, keyword coverage, latency, iteration use, and errors.

Evaluation scripts and endpoints read JSONL datasets under `eval/` and write reports under `eval/results/`.

## Guardrails

`GuardrailsService` provides deterministic first-line protection:

- prompt-injection pattern detection
- output redaction for phone numbers, emails, and ID-like values
- tool whitelist and suspicious argument detection
- explicit support for `mcp__<server>__<tool>` names

Existing services receive guardrails as optional parameters so old call paths remain unchanged.

## Observability

`TracingService` stores local trace records in SQLite:

- trace ID and parent ID
- name, status, latency, metadata
- optional model, token, and cost fields

`cost_calculator.py` centralizes model pricing. LLM and tool calls can opt into tracing through optional parameters.

Observability endpoints expose recent traces, cost summary, and recent Agent run traces.

## Compatibility

Defaults preserve existing behavior:

- no guardrails/tracing object passed means service behavior is unchanged
- guardrails and tracing are enabled at the API layer through shared services
- tests can still patch route-level services directly
- Rerank fail-soft defaults on, but hard-failure behavior remains available through settings

## Verification

Phase 7 is complete only after:

- focused P0 tests pass
- all Phase 7 tests pass
- full pytest passes
- MCP smoke test passes
- backend starts and representative endpoints respond
- real rerank/RAG smoke is either passing or clearly recorded as external service failure

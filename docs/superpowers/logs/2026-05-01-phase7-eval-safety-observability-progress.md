# Phase 7 Evaluation, Safety, and Observability Progress

## Scope

Phase 7 adds:

- Phase 6 MCP hardening
- RAG and Agent evaluation
- Guardrails
- local SQLite tracing and cost reporting

## Completion Criteria

- P0 hardening focused tests pass.
- Full pytest passes.
- MCP smoke still passes.
- Evaluation scripts and endpoints work with mocked tests.
- Guardrails cover prompt injection, PII redaction, local tools, and MCP tools.
- Observability writes traces and returns cost summary.
- Backend starts and representative endpoints respond.

## Progress

- 2026-05-01: Loaded relevant workflow skills and started with Phase 6 review-feedback validation.
- 2026-05-01: Dispatched read-only subagents for P0, Evaluation, and Guardrails/Observability codebase analysis.
- 2026-05-01: Confirmed current P0 gaps in code: MCP server error semantics, MCP tool timeout, Windows command parsing, and rerank hard failure.
- 2026-05-01: Wrote Phase 7 design, plan, and progress log.
- 2026-05-01: Added failing P0 tests for MCP error semantics, external MCP timeout, Windows MCP command parsing, and rerank fail-soft behavior.
- 2026-05-01: Implemented P0 fixes: MCP `isError=True`, MCP tool timeout, Windows parser, `rerank_fail_soft`, MCP debug guardrails, and pinned `mcp==1.27.0`.
- 2026-05-01: Verified focused P0 tests -> `30 passed`.
- 2026-05-01: Re-ran minimal Cohere rerank request; provider still returns `403 Forbidden`.
- 2026-05-01: Verified RAG service smoke with fail-soft fallback -> ingest 1 chunk, search 1 result, ask answer length 117 with 1 source.
- 2026-05-01: Added RAG LLM-as-judge metrics, agent evaluator, evaluation datasets, `run_agent_eval.py`, and `/api/v1/eval/*` routes.
- 2026-05-01: Verified evaluation-focused tests -> `15 passed`.
- 2026-05-01: Added Guardrails service plus chat/tools/research/MCP route integration with prompt-injection blocking and PII redaction.
- 2026-05-01: Verified guardrails and MCP route tests -> `27 passed`.
- 2026-05-01: Added local cost calculator, SQLite tracing service, `/api/v1/observability/*` routes, and research root trace wiring.
- 2026-05-01: Verified tracing/cost and impacted route tests -> `39 passed`.
- 2026-05-02: Re-ran full automated test suite with environment Python -> `252 passed in 17.22s`.
- 2026-05-02: Started backend on `127.0.0.1:8002` with self-connected MCP runtime and verified live endpoints across chat, extract, tools, RAG, research, memory, MCP, eval, and observability.
- 2026-05-02: Live smoke confirmed MCP tool discovery (`4 tools`), MCP invoke result (`2 + 2 -> 4`), RAG ingest/search/ask, all four research modes, memory persistence, eval endpoints, and observability cost/traces.
- 2026-05-02: `scripts.smoke_test_mcp.py` passed (`tools_discovered=4`, `calculate_result=4`).
- 2026-05-02: `scripts.smoke_test_eval.py --base-url http://127.0.0.1:8002 --mode workflow` passed.
- 2026-05-02: External Cohere rerank is still returning `403 Forbidden` in this environment; fail-soft fallback remained active during live smoke and prevented RAG failures.

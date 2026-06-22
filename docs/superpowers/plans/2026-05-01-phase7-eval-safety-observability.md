# Phase 7 Evaluation, Safety, and Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evaluation, guardrails, and local observability while hardening the Phase 6 MCP integration.

**Architecture:** Keep additions in focused services and route modules. Existing service methods accept optional guardrails/tracing parameters so direct callers and existing tests keep working. API routes own the default enabled behavior by injecting shared services.

**Tech Stack:** FastAPI, pytest, httpx, SQLite stdlib, MCP SDK, standard-library JSONL handling.

---

### Task 1: P0 Preflight Hardening

**Files:**
- Modify: `app/services/mcp/server.py`
- Modify: `app/services/tool_registry.py`
- Modify: `app/core/config.py`
- Modify: `app/services/rerank_service.py`
- Modify: `requirements.txt`
- Tests: `tests/test_mcp_server.py`, `tests/test_tool_registry_with_mcp.py`, `tests/test_mcp_config.py`, `tests/test_rerank_service.py`

- [ ] Write failing tests for MCP `isError=True`.
- [ ] Write failing tests for external MCP timeout.
- [ ] Write failing tests for Windows MCP command parsing.
- [ ] Write failing tests for rerank fail-soft/hard-fail behavior.
- [ ] Implement fixes.
- [ ] Run focused P0 tests and full pytest.

### Task 2: Evaluation Services

**Files:**
- Modify: `app/services/evaluation_service.py`
- Create: `app/services/agent_evaluator.py`
- Tests: `tests/test_evaluation_llm_judge.py`, `tests/test_agent_evaluator.py`

- [ ] Add tests for faithfulness, context precision, answer relevance, parse fallback.
- [ ] Add tests for agent run and batch evaluation.
- [ ] Implement evaluation helpers.
- [ ] Run focused evaluation tests.

### Task 3: Evaluation Data, Scripts, and API

**Files:**
- Create/modify: `eval/README.md`, `eval/rag_questions.jsonl`, `eval/agent_topics.jsonl`
- Modify: `scripts/run_rag_eval.py`
- Create: `scripts/run_agent_eval.py`
- Create: `app/api/routes/eval.py`
- Modify: `app/main.py`
- Tests: `tests/test_eval_endpoint.py`

- [ ] Add JSONL datasets.
- [ ] Extend RAG eval script with LLM judge option and result files.
- [ ] Add agent eval script.
- [ ] Add eval API route.
- [ ] Run script import checks and endpoint tests.

### Task 4: Guardrails

**Files:**
- Create: `app/services/guardrails_service.py`
- Modify: `app/core/config.py`
- Modify: `app/services/llm_service.py`
- Modify: `app/services/tool_registry.py`
- Modify: `app/api/routes/chat.py`, `tools.py`, `research.py`, `mcp.py`
- Tests: `tests/test_guardrails_service.py`, `tests/test_guardrails_integration.py`

- [ ] Add service tests for injection detection, PII redaction, and tool validation.
- [ ] Add integration tests for chat route and MCP invoke route.
- [ ] Implement service and optional integrations.
- [ ] Run focused guardrails tests.

### Task 5: Observability and Cost

**Files:**
- Create: `app/services/cost_calculator.py`
- Create: `app/services/tracing_service.py`
- Modify: `app/core/config.py`
- Modify: `app/services/llm_service.py`
- Modify: `app/services/tool_registry.py`
- Create: `app/api/routes/observability.py`
- Modify: `app/main.py`
- Tests: `tests/test_cost_calculator.py`, `tests/test_tracing_service.py`, `tests/test_observability_endpoint.py`

- [ ] Add cost tests.
- [ ] Add tracing service tests with temporary SQLite DB.
- [ ] Add observability endpoint tests.
- [ ] Implement services and optional integrations.
- [ ] Run focused observability tests.

### Task 6: Final Smoke and Documentation

**Files:**
- Create: `scripts/smoke_test_eval.py`
- Modify: `README.md` and/or execution docs
- Modify: `docs/superpowers/logs/2026-05-01-phase7-eval-safety-observability-progress.md`

- [ ] Add smoke script.
- [ ] Document MCP debug endpoint local-only warning and dependency upgrade reason.
- [ ] Run full pytest.
- [ ] Run backend smoke checks.
- [ ] Record final verification.

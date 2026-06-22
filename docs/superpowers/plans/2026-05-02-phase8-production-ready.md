# Phase 8 Production-Ready Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add streaming, simple auth, Streamlit frontend, Docker/Compose, CI, and stronger API documentation so the project is deployment-ready and easy to review.

**Architecture:** Keep backend changes additive and backward-compatible. Add a dedicated streaming path, dependency-based auth, a separate Streamlit frontend unit, and standalone deployment artifacts. Preserve existing route behavior by default and verify with targeted tests before full-suite validation.

**Tech Stack:** FastAPI, httpx, pytest, Streamlit, pandas, Docker, Docker Compose, GitHub Actions.

---

### Task 1: Phase 8 Records And Impact Mapping

**Files:**
- Create: `docs/superpowers/specs/2026-05-02-phase8-production-ready-design.md`
- Create: `docs/superpowers/plans/2026-05-02-phase8-production-ready.md`
- Create: `docs/superpowers/logs/2026-05-02-phase8-production-ready-progress.md`

- [ ] Save the design document.
- [ ] Save the implementation plan.
- [ ] Create a progress log with scope and verification goals.

### Task 2: SSE Chat Streaming

**Files:**
- Create: `tests/test_chat_stream.py`
- Create: `tests/test_chat_stream_endpoint.py`
- Modify: `app/services/llm_service.py`
- Modify: `app/api/routes/chat.py`

- [ ] Write failing tests for stream chunk parsing, `[DONE]` termination, and error handling.
- [ ] Run the new SSE tests and confirm they fail for the expected missing behavior.
- [ ] Implement `LLMService.chat_stream()` with OpenAI-compatible SSE parsing.
- [ ] Add `/api/v1/chat/stream` returning `StreamingResponse`.
- [ ] Re-run the SSE tests until they pass.

### Task 3: Optional API Key Protection

**Files:**
- Create: `tests/test_auth.py`
- Modify: `app/core/config.py`
- Create: `app/core/auth.py`
- Modify: `app/api/routes/tools.py`
- Modify: `app/api/routes/research.py`
- Modify: `app/api/routes/memory.py`

- [ ] Write failing auth tests for disabled-by-default, missing key, and valid key.
- [ ] Run the auth tests and confirm they fail correctly.
- [ ] Add `api_key_required` and `api_key` settings.
- [ ] Implement `require_api_key`.
- [ ] Apply the dependency to `/research`, `/tools`, and `/memory`.
- [ ] Re-run the auth tests until they pass.

### Task 4: Research Streaming Events

**Files:**
- Modify: `app/api/routes/research.py`
- Modify: `app/schemas/research.py` only if request parsing requires a model-level field

- [ ] Add a targeted failing test or extend an existing route test for `stream=true`.
- [ ] Implement a route-level streaming path that emits step events without breaking the existing JSON path.
- [ ] Re-run focused research route tests.

### Task 5: Streamlit Frontend

**Files:**
- Create: `frontend/app.py`
- Create: `frontend/pages/1__Chat.py`
- Create: `frontend/pages/2__RAG.py`
- Create: `frontend/pages/3__Research.py`
- Create: `frontend/pages/4__Observability.py`
- Create: `frontend/utils/api_client.py`
- Create: `frontend/utils/streaming.py`
- Create: `frontend/requirements.txt`
- Create: `frontend/README.md`

- [ ] Add the frontend file structure.
- [ ] Implement shared API client helpers.
- [ ] Implement SSE parsing helper for the chat page.
- [ ] Implement the four Streamlit pages.
- [ ] Run the frontend locally against the backend and verify page loading plus one key interaction per page.

### Task 6: Docker And Compose

**Files:**
- Create: `Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Modify: `.env.example`

- [ ] Add backend multi-stage Dockerfile.
- [ ] Add frontend Dockerfile.
- [ ] Add docker-compose service graph for qdrant, backend, frontend.
- [ ] Add `.dockerignore`.
- [ ] Extend `.env.example` with all deployment-facing variables.
- [ ] Run `docker compose config` to validate the compose file.

### Task 7: CI And OpenAPI Metadata

**Files:**
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/lint.yml`
- Modify: `app/main.py`
- Modify: key route modules with examples/tags if needed

- [ ] Add pytest workflow.
- [ ] Add ruff workflow.
- [ ] Update FastAPI metadata with title, description, version, and tag descriptions.
- [ ] Add request examples for `/research` and `/rag/ask`.
- [ ] Start the backend and verify `/docs` shows grouped routes.

### Task 8: README Overhaul And Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/logs/2026-05-02-phase8-production-ready-progress.md`
- Create: or modify any smoke command notes required by verification

- [ ] Rewrite README with overview, Mermaid architecture, quick start, Docker flow, API table, research mode comparison, evaluation instructions, test instructions, project structure, and technical decisions.
- [ ] Run full pytest.
- [ ] Run backend smoke for streaming, auth-disabled default, docs, eval, observability.
- [ ] Run `docker compose up` and verify backend, frontend, and qdrant are reachable.
- [ ] Record final verification in the progress log.

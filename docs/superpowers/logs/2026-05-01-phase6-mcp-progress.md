# Phase 6 MCP Implementation Log

## Scope

Implement MCP tools support:

- local MCP server exposing `ToolRegistry`
- external MCP stdio client
- runtime manager
- optional `ToolRegistry` integration
- MCP debug API endpoints
- stdio server script and manual smoke test

## Completion Criteria

- All previous tests still pass.
- MCP adapter, server, client, runtime, ToolRegistry integration, and endpoint tests pass.
- `scripts/run_mcp_server.py` imports and can start.
- `scripts/smoke_test_mcp.py` validates end-to-end list tools and `calculate`.
- Backend starts with MCP route registered.
- Representative local API checks pass.

## Progress

- 2026-05-01: Confirmed `mcp` package was not initially installed.
- 2026-05-01: Ran `conda run -n ai-agent pip install "mcp>=1.2.0"`; command timed out after package installation work, then verified installed version `1.27.0`.
- 2026-05-01: Inspected installed MCP SDK signatures for `Server`, `ClientSession`, `stdio_server`, `stdio_client`, `Tool`, and `TextContent`.
- 2026-05-01: Wrote Phase 6 design, implementation plan, and progress log.
- 2026-05-01: Added MCP settings red tests and verified expected failures.
- 2026-05-01: Implemented MCP settings defaults and external server parser.
- 2026-05-01: Verified `tests/test_mcp_config.py` -> `3 passed`.
- 2026-05-01: Added adapter tests, verified missing module failure, implemented OpenAI/MCP conversion, and verified `tests/test_mcp_adapter.py` -> `4 passed`.
- 2026-05-01: Added server tests, verified missing module failure, implemented MCP server wrapper, and verified `tests/test_mcp_server.py` -> `3 passed`.
- 2026-05-01: Added `scripts/run_mcp_server.py` and verified it imports.
- 2026-05-01: Added client tests, verified missing module failure, implemented stdio client connection, fixed prefix validation order, and verified `tests/test_mcp_client.py` -> `4 passed`.
- 2026-05-01: Added runtime tests, verified missing module failure, implemented runtime manager, and verified `tests/test_mcp_runtime.py` -> `5 passed`.
- 2026-05-01: Found that installing latest `mcp` with old `FastAPI 0.115.0` upgraded `starlette` to `1.0.0`, which broke FastAPI imports.
- 2026-05-01: Re-ran dependency install through Tsinghua PyPI mirror and confirmed latest compatible stack: `fastapi 0.136.1`, `mcp 1.27.0`, `starlette 1.0.0`, `pydantic 2.13.3`, `uvicorn 0.46.0`.
- 2026-05-01: Verified focused suite on upgraded stack: `36 passed`.
- 2026-05-01: Added `ToolRegistry` MCP integration tests, verified expected failures, implemented optional MCP runtime attachment, and verified `tests/test_tool_registry_with_mcp.py` -> `5 passed`.
- 2026-05-01: Added MCP endpoint tests, verified expected 404/missing module failures, implemented `/api/v1/mcp/*`, registered router, added app lifespan runtime startup/shutdown, and verified `tests/test_mcp_endpoint.py` -> `4 passed`.
- 2026-05-01: Added `scripts/smoke_test_mcp.py` and verified self-connection smoke test -> discovered 4 tools and `calculate_result=4`.
- 2026-05-01: Verified MCP/tool focused suite -> `43 passed`.
- 2026-05-01: Verified full regression suite -> `207 passed in 15.18s`.
- 2026-05-01: Started backend on `127.0.0.1:8002` and verified `/health`, `/`, `/chat`, `/extract`, `/tools/list`, `/tools/chat`, `/mcp/servers`, `/mcp/tools`, and memory error handling.
- 2026-05-01: Verified real RAG ingest succeeded with `chunk_count=5`.
- 2026-05-01: Real RAG search/ask were blocked by external rerank API returning `403 Forbidden` from `https://api.cohere.com/v2/rerank`; this is an environment credential issue, not caused by MCP changes.

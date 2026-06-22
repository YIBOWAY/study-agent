# Phase 6 MCP Design

## Goal

Add Model Context Protocol support to the learning project:

- expose the existing local tools through a stdio MCP server
- connect to optional external stdio MCP servers
- make external MCP tools available to the existing tool-calling loop
- provide API endpoints for inspecting and invoking connected MCP tools

Only MCP tools are in scope. Resources, prompts, and SSE transport are intentionally out of scope.

## Constraints

- Keep all LLM calls in `LLMService`; do not add OpenAI SDK or LangChain LLM wrappers.
- Add only the official `mcp` package as a new dependency.
- Preserve existing `ToolRegistry` behavior when no MCP runtime is attached.
- Keep existing Phase 4 and Phase 5 behavior intact.
- Use stdio transport only.

## Architecture

### Adapter

`app/services/mcp/adapter.py` contains pure conversion functions:

- OpenAI function tool schema to MCP `Tool`
- MCP `Tool` to OpenAI function tool schema with `mcp__<server>__<tool>` names

The JSON schema is passed through as the tool input schema.

### Server

`app/services/mcp/server.py` builds a stdio MCP server around `ToolRegistry`.

- `tools/list` exposes all local registry tools
- `tools/call` routes to `ToolRegistry.execute`
- tool results are returned as MCP text content
- tool errors are returned as text beginning with `ERROR:`

`scripts/run_mcp_server.py` is the external entry point for Claude Desktop, Cursor, and other MCP clients.

### Client

`app/services/mcp/client.py` manages one external stdio MCP server process.

- starts the configured command
- initializes a `ClientSession`
- discovers tools
- converts discovered tools to OpenAI format
- strips the `mcp__<server>__` prefix before invoking the remote tool

### Runtime

`app/services/mcp/runtime.py` manages all external MCP connections.

- parses configured server specs from settings
- starts all configured servers on app startup
- skips failed servers without crashing the app
- aggregates tools from all connected servers
- routes prefixed tool names to the right connection

### ToolRegistry Integration

`ToolRegistry` gains optional runtime attachment.

- local tools still behave the same when no runtime is attached
- external MCP tools appear in `get_openai_tools_schema`
- `execute("mcp__...")` routes to the MCP runtime
- `list_tools()` continues returning local `RegisteredTool` objects for compatibility

### API

`app/api/routes/mcp.py` adds:

- `GET /api/v1/mcp/servers`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/{tool_name}/invoke`

With no configured external MCP servers, these endpoints return empty server/tool lists rather than errors.

## Testing

The implementation uses focused tests for each layer:

- adapter conversion tests
- server handler tests
- client tests with mocked stdio transport/session
- runtime routing tests
- ToolRegistry compatibility and MCP routing tests
- endpoint tests
- manual smoke test script that starts this project's MCP server and calls `calculate`

Final verification includes full pytest, backend startup, and API smoke checks.

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from app.services.mcp.client import MCPClientConnection


class FakeAsyncContext:
    def __init__(self, value: Any = None, exc: Exception | None = None) -> None:
        self.value = value
        self.exc = exc
        self.closed = False

    async def __aenter__(self) -> Any:
        if self.exc is not None:
            raise self.exc
        return self.value

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.closed = True


class FakeClientSession:
    last_instance: "FakeClientSession | None" = None

    def __init__(self, read_stream: object, write_stream: object) -> None:
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.initialized = False
        self.listed = False
        self.called_with: tuple[str, dict[str, Any]] | None = None
        FakeClientSession.last_instance = self

    async def __aenter__(self) -> "FakeClientSession":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def initialize(self) -> None:
        self.initialized = True

    async def list_tools(self) -> ListToolsResult:
        self.listed = True
        return ListToolsResult(
            tools=[
                Tool(
                    name="read_file",
                    description="Read a file.",
                    inputSchema={"type": "object", "properties": {"path": {"type": "string"}}},
                )
            ]
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        self.called_with = (name, arguments)
        return CallToolResult(
            content=[TextContent(type="text", text="file contents")],
            isError=False,
        )


@pytest.mark.asyncio
async def test_mcp_client_connect_and_list() -> None:
    conn = MCPClientConnection("filesystem", "npx", ["server"])

    with (
        patch("app.services.mcp.client.stdio_client", return_value=FakeAsyncContext(("read", "write"))),
        patch("app.services.mcp.client.ClientSession", FakeClientSession),
    ):
        await conn.connect()

    tools = conn.list_tools()
    assert FakeClientSession.last_instance is not None
    assert FakeClientSession.last_instance.initialized is True
    assert FakeClientSession.last_instance.listed is True
    assert tools[0]["function"]["name"] == "mcp__filesystem__read_file"

    await conn.close()


@pytest.mark.asyncio
async def test_mcp_client_call_tool_strips_prefix() -> None:
    conn = MCPClientConnection("filesystem", "npx", ["server"])

    with (
        patch("app.services.mcp.client.stdio_client", return_value=FakeAsyncContext(("read", "write"))),
        patch("app.services.mcp.client.ClientSession", FakeClientSession),
    ):
        await conn.connect()
        result = await conn.call_tool("mcp__filesystem__read_file", {"path": "/tmp/a.txt"})

    assert result == {"result": "file contents", "is_error": False}
    assert FakeClientSession.last_instance is not None
    assert FakeClientSession.last_instance.called_with == ("read_file", {"path": "/tmp/a.txt"})

    await conn.close()


@pytest.mark.asyncio
async def test_mcp_client_rejects_wrong_prefix() -> None:
    conn = MCPClientConnection("filesystem", "npx", ["server"])

    with pytest.raises(ValueError, match="does not belong"):
        await conn.call_tool("mcp__github__read_file", {})


@pytest.mark.asyncio
async def test_mcp_client_handles_connection_error() -> None:
    conn = MCPClientConnection("broken", "missing-command", [])

    with patch(
        "app.services.mcp.client.stdio_client",
        return_value=FakeAsyncContext(exc=RuntimeError("cannot start")),
    ):
        with pytest.raises(RuntimeError, match="cannot start"):
            await conn.connect()

    assert conn.list_tools() == []
    assert conn._session is None

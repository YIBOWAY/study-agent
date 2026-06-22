from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.services.mcp.runtime import MCPRuntime


class FakeSettings:
    def __init__(self, specs: list[dict[str, Any]]) -> None:
        self.specs = specs

    def parse_external_mcp_servers(self) -> list[dict[str, Any]]:
        return self.specs


class FakeConnection:
    def __init__(self, name: str, command: str, args: list[str]) -> None:
        self.name = name
        self.command = command
        self.args = args
        self.closed = False
        if name == "broken":
            self.should_fail = True
        else:
            self.should_fail = False

    async def connect(self) -> None:
        if self.should_fail:
            raise RuntimeError("cannot connect")

    async def close(self) -> None:
        self.closed = True

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": f"mcp__{self.name}__echo",
                    "description": "Echo",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    async def call_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"result": f"{self.name}:{prefixed_name}:{arguments['value']}", "is_error": False}


@pytest.mark.asyncio
async def test_runtime_start_with_no_servers() -> None:
    runtime = MCPRuntime(FakeSettings([]))

    await runtime.start()

    assert runtime.list_servers() == []
    assert runtime.list_all_tools() == []


@pytest.mark.asyncio
async def test_runtime_start_skips_failed_server() -> None:
    runtime = MCPRuntime(
        FakeSettings(
            [
                {"name": "broken", "command": "bad", "args": []},
                {"name": "ok", "command": "python", "args": ["server.py"]},
            ]
        )
    )

    with patch("app.services.mcp.runtime.MCPClientConnection", FakeConnection):
        await runtime.start()

    assert [server["name"] for server in runtime.list_servers()] == ["ok"]


@pytest.mark.asyncio
async def test_runtime_list_all_tools_aggregates() -> None:
    runtime = MCPRuntime(
        FakeSettings(
            [
                {"name": "one", "command": "cmd", "args": []},
                {"name": "two", "command": "cmd", "args": []},
            ]
        )
    )

    with patch("app.services.mcp.runtime.MCPClientConnection", FakeConnection):
        await runtime.start()

    names = [tool["function"]["name"] for tool in runtime.list_all_tools()]
    assert names == ["mcp__one__echo", "mcp__two__echo"]


@pytest.mark.asyncio
async def test_runtime_execute_routes_to_correct_server() -> None:
    runtime = MCPRuntime(
        FakeSettings(
            [
                {"name": "one", "command": "cmd", "args": []},
                {"name": "two", "command": "cmd", "args": []},
            ]
        )
    )

    with patch("app.services.mcp.runtime.MCPClientConnection", FakeConnection):
        await runtime.start()
        result = await runtime.execute_tool("mcp__two__echo", {"value": "hello"})

    assert result == {"result": "two:mcp__two__echo:hello", "is_error": False}


@pytest.mark.asyncio
async def test_runtime_execute_rejects_unknown_server() -> None:
    runtime = MCPRuntime(FakeSettings([]))

    with pytest.raises(ValueError, match="No MCP server"):
        await runtime.execute_tool("mcp__missing__echo", {})

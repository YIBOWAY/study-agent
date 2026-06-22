from __future__ import annotations

from typing import Any

import pytest
from mcp import types

from app.schemas.tools import ToolCallRecord
from app.services.mcp.server import build_mcp_server


class FakeToolRegistry:
    def __init__(self) -> None:
        self.called_with: tuple[str, dict[str, Any]] | None = None
        self.raise_on_execute = False
        self.return_error = False

    def get_openai_tools_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Compute a math expression.",
                    "parameters": {
                        "type": "object",
                        "properties": {"expression": {"type": "string"}},
                        "required": ["expression"],
                    },
                },
            }
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolCallRecord:
        self.called_with = (name, arguments)
        if self.raise_on_execute:
            raise RuntimeError("tool exploded")
        if self.return_error:
            return ToolCallRecord(tool=name, args=arguments, result="", error="bad expression")
        return ToolCallRecord(tool=name, args=arguments, result="4", error=None)


class FakeSettings:
    mcp_server_name = "test-mcp"
    mcp_server_version = "0.1.0"


@pytest.mark.asyncio
async def test_build_mcp_server_lists_all_registry_tools() -> None:
    server = build_mcp_server(FakeToolRegistry(), FakeSettings())

    response = await server.request_handlers[types.ListToolsRequest](types.ListToolsRequest())

    assert len(response.root.tools) == 1
    assert response.root.tools[0].name == "calculate"
    assert response.root.tools[0].inputSchema["required"] == ["expression"]


@pytest.mark.asyncio
async def test_mcp_server_call_tool_success() -> None:
    registry = FakeToolRegistry()
    server = build_mcp_server(registry, FakeSettings())
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(
            name="calculate",
            arguments={"expression": "2 + 2"},
        )
    )

    response = await server.request_handlers[types.CallToolRequest](request)

    assert registry.called_with == ("calculate", {"expression": "2 + 2"})
    assert response.root.content[0].text == "4"
    assert response.root.isError is False


@pytest.mark.asyncio
async def test_mcp_server_call_tool_error() -> None:
    registry = FakeToolRegistry()
    registry.raise_on_execute = True
    server = build_mcp_server(registry, FakeSettings())
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(
            name="calculate",
            arguments={"expression": "2 + 2"},
        )
    )

    response = await server.request_handlers[types.CallToolRequest](request)

    assert response.root.content[0].text == "tool exploded"
    assert response.root.isError is True


@pytest.mark.asyncio
async def test_mcp_server_call_tool_record_error_sets_protocol_error() -> None:
    registry = FakeToolRegistry()
    registry.return_error = True
    server = build_mcp_server(registry, FakeSettings())
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(
            name="calculate",
            arguments={"expression": "bad"},
        )
    )

    response = await server.request_handlers[types.CallToolRequest](request)

    assert response.root.content[0].text == "bad expression"
    assert response.root.isError is True

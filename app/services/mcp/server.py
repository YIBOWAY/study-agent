from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

from app.services.mcp.adapter import openai_tool_to_mcp_tool

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.services.tool_registry import ToolRegistry


def build_mcp_server(tool_registry: "ToolRegistry", settings: "Settings") -> Server:
    server = Server(name=settings.mcp_server_name, version=settings.mcp_server_version)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            openai_tool_to_mcp_tool(tool)
            for tool in tool_registry.get_openai_tools_schema()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        try:
            record = await tool_registry.execute(name, arguments)
            if record.error:
                return CallToolResult(
                    content=[TextContent(type="text", text=record.error)],
                    isError=True,
                )
            return CallToolResult(
                content=[TextContent(type="text", text=record.result)],
                isError=False,
            )
        except Exception as exc:
            return CallToolResult(
                content=[TextContent(type="text", text=str(exc))],
                isError=True,
            )

    return server


async def run_stdio_server(tool_registry: "ToolRegistry", settings: "Settings") -> None:
    server = build_mcp_server(tool_registry, settings)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

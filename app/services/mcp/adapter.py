from __future__ import annotations

from typing import Any

from mcp.types import Tool


def openai_tool_to_mcp_tool(openai_tool: dict[str, Any]) -> Tool:
    function = openai_tool.get("function", {})
    name = str(function.get("name") or "")
    description = str(function.get("description") or "")
    parameters = function.get("parameters") or {"type": "object", "properties": {}}
    if not isinstance(parameters, dict):
        parameters = {"type": "object", "properties": {}}

    return Tool(name=name, description=description, inputSchema=parameters)


def mcp_tool_to_openai_tool(mcp_tool: Tool, server_name: str) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": f"mcp__{server_name}__{mcp_tool.name}",
            "description": mcp_tool.description or "",
            "parameters": mcp_tool.inputSchema,
        },
    }

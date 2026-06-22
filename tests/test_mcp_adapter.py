from mcp.types import Tool

from app.services.mcp.adapter import mcp_tool_to_openai_tool, openai_tool_to_mcp_tool


def _openai_tool() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Compute a math expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Expression to evaluate."}
                },
                "required": ["expression"],
            },
        },
    }


def test_openai_to_mcp_basic() -> None:
    tool = openai_tool_to_mcp_tool(_openai_tool())

    assert tool.name == "calculate"
    assert tool.description == "Compute a math expression."
    assert tool.inputSchema["properties"]["expression"]["type"] == "string"


def test_openai_to_mcp_required_fields() -> None:
    tool = openai_tool_to_mcp_tool(_openai_tool())

    assert tool.inputSchema["required"] == ["expression"]


def test_mcp_to_openai_with_prefix() -> None:
    mcp_tool = Tool(
        name="read_file",
        description="Read a file.",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )

    openai_tool = mcp_tool_to_openai_tool(mcp_tool, "filesystem")

    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "mcp__filesystem__read_file"
    assert openai_tool["function"]["parameters"]["required"] == ["path"]


def test_mcp_to_openai_round_trip() -> None:
    mcp_tool = openai_tool_to_mcp_tool(_openai_tool())
    openai_tool = mcp_tool_to_openai_tool(mcp_tool, "local")

    assert openai_tool["function"]["name"] == "mcp__local__calculate"
    assert openai_tool["function"]["description"] == "Compute a math expression."
    assert openai_tool["function"]["parameters"] == _openai_tool()["function"]["parameters"]

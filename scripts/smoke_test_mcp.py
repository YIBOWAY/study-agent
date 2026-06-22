"""
Manual MCP smoke test.

Starts this project's MCP server through stdio, connects to it as an MCP client,
lists exposed tools, and calls the local calculate tool.
"""

from __future__ import annotations

import asyncio
import sys

from app.services.mcp.client import MCPClientConnection


async def main() -> None:
    conn = MCPClientConnection(
        name="self",
        command=sys.executable,
        args=["-m", "scripts.run_mcp_server"],
    )
    await conn.connect()
    try:
        tools = conn.list_tools()
        names = [tool["function"]["name"] for tool in tools]
        if "mcp__self__calculate" not in names:
            raise RuntimeError(f"calculate tool was not exposed. Tools: {names}")

        result = await conn.call_tool("mcp__self__calculate", {"expression": "2 + 2"})
        if result != {"result": "4", "is_error": False}:
            raise RuntimeError(f"unexpected calculate result: {result}")

        print("MCP smoke test passed")
        print(f"tools_discovered={len(tools)}")
        print(f"calculate_result={result['result']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Start this project's MCP server in stdio mode.

Example external client config:
{
  "mcpServers": {
    "research-agent": {
      "command": "python",
      "args": ["-m", "scripts.run_mcp_server"],
      "cwd": "E:/programs/AI_Agent_program/8w-plan"
    }
  }
}
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.services.mcp.server import run_stdio_server
from app.services.tool_registry import ToolRegistry


async def main() -> None:
    settings = get_settings()
    registry = ToolRegistry(settings=settings)
    await run_stdio_server(registry, settings)


if __name__ == "__main__":
    asyncio.run(main())

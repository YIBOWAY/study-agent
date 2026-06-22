from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from app.core.config import get_settings
from app.services.mcp.client import MCPClientConnection

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)


class MCPRuntime:
    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self._connections: dict[str, MCPClientConnection] = {}

    async def start(self) -> None:
        for spec in self.settings.parse_external_mcp_servers():
            conn = MCPClientConnection(spec["name"], spec["command"], spec["args"])
            try:
                await conn.connect()
            except Exception as exc:
                logger.warning("MCP server '%s' failed to connect: %s", spec["name"], exc)
                continue
            self._connections[spec["name"]] = conn

    async def stop(self) -> None:
        for conn in list(self._connections.values()):
            await conn.close()
        self._connections.clear()

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "tool_count": len(conn.list_tools()),
                "tools": conn.list_tools(),
            }
            for name, conn in self._connections.items()
        ]

    def list_all_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for conn in self._connections.values():
            tools.extend(conn.list_tools())
        return tools

    async def execute_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        server_name = self._extract_server_name(prefixed_name)
        conn = self._connections.get(server_name)
        if conn is None:
            raise ValueError(f"No MCP server is connected for tool '{prefixed_name}'.")
        return await conn.call_tool(prefixed_name, arguments)

    @staticmethod
    def _extract_server_name(prefixed_name: str) -> str:
        parts = prefixed_name.split("__", 2)
        if len(parts) != 3 or parts[0] != "mcp" or not parts[1] or not parts[2]:
            raise ValueError(f"Invalid MCP tool name: {prefixed_name}")
        return parts[1]


_runtime: MCPRuntime | None = None
_runtime_lock = asyncio.Lock()


def get_mcp_runtime() -> MCPRuntime:
    global _runtime
    if _runtime is None:
        _runtime = MCPRuntime(get_settings())
    return _runtime


async def init_mcp_runtime(settings: "Settings") -> None:
    global _runtime
    async with _runtime_lock:
        if _runtime is not None:
            await _runtime.stop()
        _runtime = MCPRuntime(settings)
        await _runtime.start()


async def shutdown_mcp_runtime() -> None:
    global _runtime
    async with _runtime_lock:
        if _runtime is not None:
            await _runtime.stop()
        _runtime = None

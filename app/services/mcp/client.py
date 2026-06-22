from __future__ import annotations

from contextlib import AsyncExitStack
import json
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

from app.services.mcp.adapter import mcp_tool_to_openai_tool


class MCPClientConnection:
    def __init__(self, name: str, command: str, args: list[str]) -> None:
        self.name = name
        self.command = command
        self.args = args
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._tools: list[dict[str, Any]] = []

    async def connect(self) -> None:
        exit_stack = AsyncExitStack()
        try:
            server_params = StdioServerParameters(command=self.command, args=self.args)
            read_stream, write_stream = await exit_stack.enter_async_context(stdio_client(server_params))
            session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            response = await session.list_tools()
            self._tools = [
                mcp_tool_to_openai_tool(tool, self.name)
                for tool in response.tools
            ]
            self._session = session
            self._exit_stack = exit_stack
        except Exception:
            await exit_stack.aclose()
            self._session = None
            self._exit_stack = None
            self._tools = []
            raise

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        prefix = f"mcp__{self.name}__"
        if not tool_name.startswith(prefix):
            raise ValueError(f"Tool '{tool_name}' does not belong to MCP server '{self.name}'.")

        if self._session is None:
            raise RuntimeError(f"MCP server '{self.name}' is not connected.")

        remote_name = tool_name.removeprefix(prefix)
        result = await self._session.call_tool(remote_name, arguments)
        return {
            "result": self._content_to_text(result.content),
            "is_error": bool(result.isError),
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    async def close(self) -> None:
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
        self._session = None
        self._exit_stack = None
        self._tools = []

    @staticmethod
    def _content_to_text(content: list[Any]) -> str:
        lines: list[str] = []
        for item in content:
            if isinstance(item, TextContent):
                lines.append(item.text)
            elif hasattr(item, "model_dump"):
                lines.append(json.dumps(item.model_dump(), ensure_ascii=False))
            else:
                lines.append(str(item))
        return "\n".join(lines)

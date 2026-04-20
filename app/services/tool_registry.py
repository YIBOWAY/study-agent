from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import asyncio
import json
from typing import TYPE_CHECKING, Any

from app.core.config import Settings, get_settings
from app.schemas.tools import ToolCallRecord, ToolInfo
from app.services.tools import (
    build_calculate_tool,
    build_code_executor_tool,
    build_get_current_time_tool,
    build_search_knowledge_base_tool,
    build_web_search_tool,
)

if TYPE_CHECKING:
    from app.services.rag_service import RAGService

ToolHandler = Callable[[dict[str, Any]], Awaitable[str | dict[str, Any]]]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    def __init__(
        self,
        settings: Settings | None = None,
        rag_service: "RAGService" | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if rag_service is None:
            from app.services.rag_service import RAGService

            rag_service = RAGService()
        self.rag_service = rag_service
        self._tools: dict[str, RegisteredTool] = {}
        self._register_defaults()

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        parameters_schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            parameters=parameters_schema,
            handler=handler,
        )

    def list_tools(self, enabled_tools: list[str] | None = None) -> list[RegisteredTool]:
        if enabled_tools is None:
            return list(self._tools.values())
        missing = [name for name in enabled_tools if name not in self._tools]
        if missing:
            raise ValueError(f"Unknown tool(s): {', '.join(missing)}")
        return [self._tools[name] for name in enabled_tools]

    def get_openai_tools_schema(self, enabled_tools: list[str] | None = None) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self.list_tools(enabled_tools)
        ]

    def get_tool_infos(self, enabled_tools: list[str] | None = None) -> list[ToolInfo]:
        return [
            ToolInfo(name=tool.name, description=tool.description, parameters=tool.parameters)
            for tool in self.list_tools(enabled_tools)
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolCallRecord:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' is not registered.")

        try:
            raw_result = await asyncio.wait_for(
                tool.handler(arguments),
                timeout=self.settings.tool_call_timeout,
            )
            result = self._serialize_result(raw_result)
            return ToolCallRecord(tool=name, args=arguments, result=result)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return ToolCallRecord(
                tool=name,
                args=arguments,
                result="",
                error="Tool execution timed out.",
            )
        except Exception as exc:
            return ToolCallRecord(
                tool=name,
                args=arguments,
                result="",
                error=str(exc),
            )

    def _register_defaults(self) -> None:
        time_tool = build_get_current_time_tool()
        calculate_tool = build_calculate_tool()
        search_tool = build_search_knowledge_base_tool(self.rag_service)
        web_search_tool = build_web_search_tool(self.settings)
        tools = [time_tool, calculate_tool, search_tool, web_search_tool]
        if self.settings.enable_code_execution_tool:
            tools.append(build_code_executor_tool())
        for tool in tools:
            self.register_tool(
                name=tool.name,
                description=tool.description,
                parameters_schema=tool.parameters,
                handler=tool.handler,
            )

    @staticmethod
    def _serialize_result(result: str | dict[str, Any]) -> str:
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import asyncio
import hashlib
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
    from app.services.guardrails_service import GuardrailsService
    from app.services.rag_service import RAGService
    from app.services.tracing_service import TracingService

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
        self._mcp_runtime: Any | None = None
        self._tracing_service: "TracingService | None" = None
        self._register_defaults()

    def attach_mcp_runtime(self, runtime: Any) -> None:
        self._mcp_runtime = runtime

    def attach_tracing_service(self, tracing: "TracingService | None") -> None:
        self._tracing_service = tracing

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
        if enabled_tools is not None:
            return self._get_selected_openai_tools_schema(enabled_tools)

        return [
            self._registered_tool_to_openai_schema(tool)
            for tool in self.list_tools(enabled_tools)
        ] + self._list_mcp_openai_tools()

    def get_tool_infos(self, enabled_tools: list[str] | None = None) -> list[ToolInfo]:
        return [
            ToolInfo(
                name=tool["function"]["name"],
                description=tool["function"].get("description", ""),
                parameters=tool["function"].get("parameters", {}),
            )
            for tool in self.get_openai_tools_schema(enabled_tools)
        ]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        guardrails: "GuardrailsService | None" = None,
        tracing: "TracingService | None" = None,
    ) -> ToolCallRecord:
        active_tracing = tracing or self._tracing_service
        if active_tracing is None:
            return await self._execute_without_tracing(name, arguments, guardrails)

        async with active_tracing.trace(
            "tool_execute",
            {
                "tool": name,
                "arguments_hash": self._hash_arguments(arguments),
            },
        ) as ctx:
            record = await self._execute_without_tracing(name, arguments, guardrails)
            if record.error:
                ctx.set("status", "error")
                ctx.set("error_message", record.error)
            return record

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

    @staticmethod
    def _registered_tool_to_openai_schema(tool: RegisteredTool) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    def _list_mcp_openai_tools(self) -> list[dict[str, Any]]:
        if self._mcp_runtime is None:
            return []
        return self._mcp_runtime.list_all_tools()

    def _get_selected_openai_tools_schema(self, enabled_tools: list[str]) -> list[dict[str, Any]]:
        mcp_tools_by_name = {
            item["function"]["name"]: item
            for item in self._list_mcp_openai_tools()
        }
        missing: list[str] = []
        selected: list[dict[str, Any]] = []

        for name in enabled_tools:
            if name.startswith("mcp__"):
                mcp_tool = mcp_tools_by_name.get(name)
                if mcp_tool is None:
                    missing.append(name)
                else:
                    selected.append(mcp_tool)
                continue

            local_tool = self._tools.get(name)
            if local_tool is None:
                missing.append(name)
            else:
                selected.append(self._registered_tool_to_openai_schema(local_tool))

        if missing:
            raise ValueError(f"Unknown tool(s): {', '.join(missing)}")
        return selected

    async def _execute_mcp_tool(self, name: str, arguments: dict[str, Any]) -> ToolCallRecord:
        if self._mcp_runtime is None:
            raise ValueError("MCP runtime is not attached.")

        try:
            response = await asyncio.wait_for(
                self._mcp_runtime.execute_tool(name, arguments),
                timeout=self.settings.tool_call_timeout,
            )
        except TimeoutError:
            return ToolCallRecord(
                tool=name,
                args=arguments,
                result="",
                error="MCP tool execution timed out.",
            )
        result = str(response.get("result") or "")
        error = result if response.get("is_error") else None
        return ToolCallRecord(tool=name, args=arguments, result=result, error=error)

    async def _execute_without_tracing(
        self,
        name: str,
        arguments: dict[str, Any],
        guardrails: "GuardrailsService | None",
    ) -> ToolCallRecord:
        if guardrails is not None:
            validation = guardrails.validate_tool_call(name, arguments)
            if not validation["safe"]:
                return ToolCallRecord(
                    tool=name,
                    args=arguments,
                    result="",
                    error=str(validation["reason"]),
                )

        if name.startswith("mcp__"):
            return await self._execute_mcp_tool(name, arguments)

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

    @staticmethod
    def _hash_arguments(arguments: dict[str, Any]) -> str:
        payload = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

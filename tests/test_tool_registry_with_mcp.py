from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app.core.config import Settings
from app.services.tool_registry import ToolRegistry


class FakeRAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [],
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v4.0-pro",
        }


class FakeMCPRuntime:
    def __init__(self) -> None:
        self.called_with: tuple[str, dict[str, Any]] | None = None

    def list_all_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "mcp__filesystem__read_file",
                    "description": "Read a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            }
        ]

    async def execute_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.called_with = (prefixed_name, arguments)
        return {"result": "file contents", "is_error": False}


class SlowMCPRuntime(FakeMCPRuntime):
    async def execute_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(2)
        return {"result": "late", "is_error": False}


def _registry() -> ToolRegistry:
    return ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )


def _registry_with_timeout(timeout: int) -> ToolRegistry:
    return ToolRegistry(
        settings=Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            tool_call_timeout=timeout,
        ),
        rag_service=FakeRAGService(),
    )


def test_tool_registry_without_mcp_unchanged() -> None:
    registry = _registry()

    assert [tool.name for tool in registry.list_tools()] == [
        "get_current_time",
        "calculate",
        "search_knowledge_base",
        "web_search",
    ]
    assert [tool["function"]["name"] for tool in registry.get_openai_tools_schema()] == [
        "get_current_time",
        "calculate",
        "search_knowledge_base",
        "web_search",
    ]


def test_tool_registry_with_mcp_lists_combined_tools() -> None:
    registry = _registry()
    registry.attach_mcp_runtime(FakeMCPRuntime())

    names = [tool["function"]["name"] for tool in registry.get_openai_tools_schema()]
    info_names = [tool.name for tool in registry.get_tool_infos()]

    assert names == [
        "get_current_time",
        "calculate",
        "search_knowledge_base",
        "web_search",
        "mcp__filesystem__read_file",
    ]
    assert info_names[-1] == "mcp__filesystem__read_file"


def test_tool_registry_with_mcp_filters_external_tools() -> None:
    registry = _registry()
    registry.attach_mcp_runtime(FakeMCPRuntime())

    tools = registry.get_openai_tools_schema(["mcp__filesystem__read_file"])

    assert [tool["function"]["name"] for tool in tools] == ["mcp__filesystem__read_file"]


@pytest.mark.asyncio
async def test_tool_registry_with_mcp_routes_external_tool() -> None:
    registry = _registry()
    runtime = FakeMCPRuntime()
    registry.attach_mcp_runtime(runtime)

    result = await registry.execute("mcp__filesystem__read_file", {"path": "/tmp/a.txt"})

    assert runtime.called_with == ("mcp__filesystem__read_file", {"path": "/tmp/a.txt"})
    assert result.tool == "mcp__filesystem__read_file"
    assert result.result == "file contents"
    assert result.error is None


@pytest.mark.asyncio
async def test_tool_registry_rejects_external_tool_without_runtime() -> None:
    registry = _registry()

    with pytest.raises(ValueError, match="MCP runtime is not attached"):
        await registry.execute("mcp__filesystem__read_file", {})


@pytest.mark.asyncio
async def test_tool_registry_mcp_tool_timeout_returns_error() -> None:
    registry = _registry_with_timeout(1)
    registry.attach_mcp_runtime(SlowMCPRuntime())

    result = await registry.execute("mcp__filesystem__read_file", {"path": "/tmp/a.txt"})

    assert result.tool == "mcp__filesystem__read_file"
    assert result.result == ""
    assert result.error == "MCP tool execution timed out."

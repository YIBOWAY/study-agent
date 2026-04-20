import asyncio

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


@pytest.mark.asyncio
async def test_registry_exports_openai_tools_schema() -> None:
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )

    tools = registry.get_openai_tools_schema()

    names = [item["function"]["name"] for item in tools]
    assert names == [
        "get_current_time",
        "calculate",
        "search_knowledge_base",
        "web_search",
    ]


@pytest.mark.asyncio
async def test_registry_can_enable_code_execution_tool() -> None:
    registry = ToolRegistry(
        settings=Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            enable_code_execution_tool=True,
        ),
        rag_service=FakeRAGService(),
    )

    names = [item["function"]["name"] for item in registry.get_openai_tools_schema()]

    assert "execute_python" in names


@pytest.mark.asyncio
async def test_registry_executes_registered_tool() -> None:
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )

    result = await registry.execute("calculate", {"expression": "23 * 47"})

    assert result.tool == "calculate"
    assert result.result == "1081"
    assert result.error is None


def test_registry_rejects_unknown_tool_in_list() -> None:
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )

    with pytest.raises(ValueError, match="Unknown tool"):
        registry.get_openai_tools_schema(["missing_tool"])


@pytest.mark.asyncio
async def test_registry_rejects_unknown_tool_execution() -> None:
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )

    with pytest.raises(ValueError, match="not registered"):
        await registry.execute("missing_tool", {})


def test_registry_rejects_duplicate_registration() -> None:
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key"),
        rag_service=FakeRAGService(),
    )

    with pytest.raises(ValueError, match="already registered"):
        registry.register_tool(
            name="calculate",
            description="duplicate",
            parameters_schema={"type": "object", "properties": {}},
            handler=lambda _: None,
        )


@pytest.mark.asyncio
async def test_registry_returns_timeout_error_for_slow_tool() -> None:
    registry = ToolRegistry(
        settings=Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            tool_call_timeout=1,
        ),
        rag_service=FakeRAGService(),
    )

    async def slow_tool(_: dict[str, object]) -> str:
        await asyncio.sleep(2)
        return "done"

    registry.register_tool(
        name="slow_tool",
        description="slow",
        parameters_schema={"type": "object", "properties": {}},
        handler=slow_tool,
    )

    result = await registry.execute("slow_tool", {})

    assert result.error == "Tool execution timed out."
    assert result.result == ""

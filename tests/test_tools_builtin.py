from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.tools.calculate import build_calculate_tool
from app.services.tools.code_executor import build_code_executor_tool
from app.services.tools.get_current_time import build_get_current_time_tool
from app.services.tools.search_knowledge_base import build_search_knowledge_base_tool
from app.services.tools.web_search import build_web_search_tool


class DummyResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self) -> dict[str, object]:
        return self._payload


class FakeRAGService:
    def __init__(self, results: list[dict[str, object]] | None = None) -> None:
        self.results = results or []
        self.calls: list[tuple[str, int, str | None]] = []

    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        self.calls.append((query, top_k, document_id))
        return {
            "results": self.results,
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v4.0-pro",
        }


@pytest.mark.asyncio
async def test_calculate_supports_safe_expression() -> None:
    tool = build_calculate_tool()

    result = await tool.handler({"expression": "23 * 47"})

    assert result == "1081"


@pytest.mark.asyncio
async def test_calculate_rejects_injection() -> None:
    tool = build_calculate_tool()

    with pytest.raises(ValueError, match="not allowed"):
        await tool.handler({"expression": "__import__('os')"})


@pytest.mark.asyncio
async def test_calculate_rejects_too_long_expression() -> None:
    tool = build_calculate_tool()

    with pytest.raises(ValueError, match="too long"):
        await tool.handler({"expression": "1" * 201})


@pytest.mark.asyncio
async def test_get_current_time_defaults_timezone() -> None:
    tool = build_get_current_time_tool()

    result = await tool.handler({})

    assert isinstance(result, str)
    assert result


@pytest.mark.asyncio
async def test_get_current_time_rejects_invalid_timezone() -> None:
    tool = build_get_current_time_tool()

    with pytest.raises(ValueError, match="Invalid timezone"):
        await tool.handler({"timezone": "Mars/Base"})


@pytest.mark.asyncio
async def test_search_knowledge_base_summarizes_results() -> None:
    rag_service = FakeRAGService(
        results=[
            {
                "text": "Revenue grew 20% year over year.",
                "source_name": "guide.pdf",
                "page_number": 2,
            }
        ]
    )
    tool = build_search_knowledge_base_tool(rag_service)

    result = await tool.handler({"query": "revenue", "top_k": 3, "document_id": "doc-1"})

    assert rag_service.calls == [("revenue", 3, "doc-1")]
    assert "guide.pdf" in result
    assert "Revenue grew 20%" in result




@patch("app.services.tools.web_search.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_web_search_success(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(
        {
            "results": [
                {
                    "title": "RAG chunking guide",
                    "url": "https://example.com/rag",
                    "content": "Chunking strategy affects retrieval quality.",
                }
            ]
        }
    )
    mock_client.return_value.__aenter__.return_value = client_instance
    tool = build_web_search_tool(
        Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key", tavily_api_key="tvly")
    )

    result = await tool.handler({"query": "rag chunking", "max_results": 3})

    assert "RAG chunking guide" in result
    assert "https://example.com/rag" in result
    assert "retrieval quality" in result


@patch("app.services.tools.web_search.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_web_search_empty(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"results": []})
    mock_client.return_value.__aenter__.return_value = client_instance
    tool = build_web_search_tool(
        Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key", tavily_api_key="tvly")
    )

    result = await tool.handler({"query": "rag chunking"})

    assert result == "No web search results found."


@patch("app.services.tools.web_search.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_web_search_api_error(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"message": "rate limit"}, status_code=429)
    mock_client.return_value.__aenter__.return_value = client_instance
    tool = build_web_search_tool(
        Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key", tavily_api_key="tvly")
    )

    with pytest.raises(ValueError, match="429"):
        await tool.handler({"query": "rag chunking"})


@pytest.mark.asyncio
async def test_web_search_empty_query() -> None:
    tool = build_web_search_tool(
        Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key", tavily_api_key="tvly")
    )

    with pytest.raises(ValueError, match="query is required"):
        await tool.handler({"query": ""})


@pytest.mark.asyncio
async def test_code_executor_success() -> None:
    tool = build_code_executor_tool()

    result = await tool.handler({"code": "print(1 + 1)"})

    assert "Exit code: 0" in result
    assert "2" in result


@pytest.mark.asyncio
async def test_code_executor_timeout() -> None:
    tool = build_code_executor_tool()

    with pytest.raises(ValueError, match="timed out"):
        await tool.handler({"code": "while True:\n    pass", "timeout": 1})


@pytest.mark.asyncio
async def test_code_executor_blocked_keyword() -> None:
    tool = build_code_executor_tool()

    with pytest.raises(ValueError, match="import os"):
        await tool.handler({"code": "import os\nprint('hi')"})


@pytest.mark.asyncio
async def test_code_executor_too_long() -> None:
    tool = build_code_executor_tool()

    with pytest.raises(ValueError, match="too long"):
        await tool.handler({"code": "a" * 5001})


@pytest.mark.asyncio
async def test_code_executor_stderr() -> None:
    tool = build_code_executor_tool()

    result = await tool.handler({"code": "print('oops'"})

    assert "Exit code:" in result
    assert "SyntaxError" in result

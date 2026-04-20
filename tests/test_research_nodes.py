from unittest.mock import AsyncMock

import pytest

from app.core.config import Settings
from app.services.research.nodes import (
    make_evaluate_results_node,
    make_generate_report_node,
    make_refine_query_node,
    make_rewrite_query_node,
    make_search_node,
)
from app.services.research.state import ResearchState
from app.services.tool_registry import ToolRegistry


class ResultObject:
    def __init__(self, text: str, score: float, source_name: str) -> None:
        self.text = text
        self.score = score
        self.source_name = source_name


class FakeRAGService:
    def __init__(self, results: list[object] | None = None, error: Exception | None = None) -> None:
        self.results = results or []
        self.error = error

    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        if self.error is not None:
            raise self.error
        return {
            "results": self.results,
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v4.0-pro",
        }


def build_state() -> ResearchState:
    return {
        "topic": "RAG chunking impact",
        "queries": [],
        "search_results": [],
        "report": "",
        "steps": [],
        "iteration": 0,
        "max_iterations": 3,
        "evaluation": "",
        "top_k": 5,
    }


@pytest.mark.asyncio
async def test_rewrite_query_appends_query() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "chunking strategy rag retrieval"}
    node = make_rewrite_query_node(llm_service)

    result = await node(build_state())

    assert result["queries"] == ["chunking strategy rag retrieval"]
    assert result["steps"][0]["node"] == "rewrite_query"


@pytest.mark.asyncio
async def test_search_merges_knowledge_base_and_web_results() -> None:
    rag_service = FakeRAGService(results=[{"text": "KB hit", "score": 0.9, "source_name": "guide.pdf"}])
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm", rerank_api_key="rerank", tavily_api_key="tvly"),
        rag_service=rag_service,
    )
    registry.execute = AsyncMock(
        return_value=type("ToolRecord", (), {"result": "[1] Web hit\nURL: https://example.com\nContent: Web snippet", "error": None})()
    )
    state = build_state()
    state["queries"] = ["chunking strategy"]
    node = make_search_node(rag_service, registry)

    result = await node(state)

    assert len(result["search_results"]) == 2
    assert result["iteration"] == 1


@pytest.mark.asyncio
async def test_search_returns_web_results_when_rag_fails() -> None:
    rag_service = FakeRAGService(error=RuntimeError("rag failed"))
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm", rerank_api_key="rerank", tavily_api_key="tvly"),
        rag_service=FakeRAGService(),
    )
    registry.execute = AsyncMock(
        return_value=type("ToolRecord", (), {"result": "[1] Web hit\nURL: https://example.com\nContent: Web snippet", "error": None})()
    )
    state = build_state()
    state["queries"] = ["chunking strategy"]
    node = make_search_node(rag_service, registry)

    result = await node(state)

    assert len(result["search_results"]) == 1
    assert any(step["node"] == "search_knowledge_base" for step in result["steps"])


@pytest.mark.asyncio
async def test_search_normalizes_object_results_from_knowledge_base() -> None:
    rag_service = FakeRAGService(results=[ResultObject("KB hit", 0.8, "guide.pdf")])
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm", rerank_api_key="rerank", tavily_api_key=""),
        rag_service=rag_service,
    )
    state = build_state()
    state["queries"] = ["chunking strategy"]
    node = make_search_node(rag_service, registry)

    result = await node(state)

    assert result["search_results"][0]["title"] == "guide.pdf"
    assert result["search_results"][0]["text_snippet"] == "KB hit"


@pytest.mark.asyncio
async def test_search_skips_web_without_tavily_key() -> None:
    rag_service = FakeRAGService(results=[{"text": "KB hit", "score": 0.9, "source_name": "guide.pdf"}])
    registry = ToolRegistry(
        settings=Settings(_env_file=None, llm_api_key="llm", rerank_api_key="rerank", tavily_api_key=""),
        rag_service=rag_service,
    )
    state = build_state()
    state["queries"] = ["chunking strategy"]
    node = make_search_node(rag_service, registry)

    result = await node(state)

    assert len(result["search_results"]) == 1
    assert any(step["node"] == "web_search" for step in result["steps"])


@pytest.mark.asyncio
async def test_evaluate_results_sets_evaluation() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": '{"evaluation": "sufficient", "reason": "enough"}'}
    node = make_evaluate_results_node(llm_service)
    state = build_state()
    state["search_results"] = [
        {
            "source": "knowledge_base",
            "query": "q",
            "text_snippet": "evidence",
            "score": 0.9,
            "title": "guide",
            "url": None,
        }
    ]

    result = await node(state)

    assert result["evaluation"] == "sufficient"


@pytest.mark.asyncio
async def test_evaluate_results_forces_sufficient_at_iteration_limit() -> None:
    llm_service = AsyncMock()
    node = make_evaluate_results_node(llm_service)
    state = build_state()
    state["iteration"] = 3

    result = await node(state)

    assert result["evaluation"] == "sufficient"
    llm_service.chat.assert_not_called()


@pytest.mark.asyncio
async def test_refine_query_appends_new_query() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "semantic splitting methods"}
    node = make_refine_query_node(llm_service)
    state = build_state()
    state["queries"] = ["chunking strategy"]

    result = await node(state)

    assert result["queries"] == ["semantic splitting methods"]


@pytest.mark.asyncio
async def test_generate_report_sets_report() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "# Report\n\nSummary"}
    node = make_generate_report_node(llm_service)
    state = build_state()
    state["search_results"] = [
        {
            "source": "knowledge_base",
            "query": "q",
            "text_snippet": "evidence",
            "score": 0.9,
            "title": "guide",
            "url": None,
        }
    ]

    result = await node(state)

    assert result["report"] == "# Report\n\nSummary"

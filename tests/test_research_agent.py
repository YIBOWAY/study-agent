from unittest.mock import AsyncMock

import pytest

from app.services.research.agent import run_agent


class FakeRAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [
                {
                    "text": "Chunking affects retrieval quality.",
                    "score": 0.9,
                    "source_name": "guide.pdf",
                }
            ],
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v4.0-pro",
        }


class FakeToolRegistry:
    def __init__(self) -> None:
        self.settings = type("Settings", (), {"tavily_api_key": ""})()

    async def execute(self, name: str, arguments: dict[str, object]) -> object:
        raise AssertionError("web search should be skipped when no Tavily key is configured")


@pytest.mark.asyncio
async def test_run_agent_stops_when_first_evaluation_is_sufficient() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": "chunking strategy rag retrieval"},
        {"reply": '{"evaluation": "sufficient", "reason": "enough evidence"}'},
        {"reply": "# Report\n\nSummary"},
    ]

    result = await run_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
    )

    assert result["iterations_used"] == 1
    assert result["queries"] == ["chunking strategy rag retrieval"]
    assert result["search_result_count"] == 1
    assert result["steps"][-1]["node"] == "generate_report"


@pytest.mark.asyncio
async def test_run_agent_refines_query_once_before_report() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": "chunking strategy rag retrieval"},
        {"reply": '{"evaluation": "needs_more", "reason": "need another angle"}'},
        {"reply": "semantic splitting methods"},
        {"reply": '{"evaluation": "sufficient", "reason": "enough evidence"}'},
        {"reply": "# Report\n\nSummary"},
    ]

    result = await run_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
    )

    assert result["iterations_used"] == 2
    assert result["queries"] == ["chunking strategy rag retrieval", "semantic splitting methods"]
    assert result["search_result_count"] == 2
    assert [step["node"] for step in result["steps"]].count("refine_query") == 1


@pytest.mark.asyncio
async def test_run_agent_stops_at_max_iterations() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": "chunking strategy rag retrieval"},
        {"reply": '{"evaluation": "needs_more", "reason": "need another angle"}'},
        {"reply": "semantic splitting methods"},
        {"reply": "# Report\n\nSummary"},
    ]

    result = await run_agent(
        topic="RAG chunking impact",
        max_iterations=2,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
    )

    assert result["iterations_used"] == 2
    assert result["steps"][-1]["node"] == "generate_report"

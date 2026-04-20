from unittest.mock import AsyncMock

import pytest

from app.services.research.workflow import run_workflow


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
async def test_run_workflow_executes_fixed_path_once() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": "chunking strategy rag retrieval"},
        {"reply": "# Report\n\nSummary"},
    ]

    result = await run_workflow(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
    )

    assert result["report"] == "# Report\n\nSummary"
    assert result["queries"] == ["chunking strategy rag retrieval"]
    assert result["iterations_used"] == 1
    assert result["search_result_count"] == 1
    assert [step["node"] for step in result["steps"]] == [
        "rewrite_query",
        "search_knowledge_base",
        "web_search",
        "generate_report",
    ]

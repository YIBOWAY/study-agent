from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.multi_agent.graph import run_multi_agent


class FakeRAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [
                {
                    "text": "Chunk overlap improves boundary recall.",
                    "score": 0.92,
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


class FakeMemoryService:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []
        self.session_calls = 0
        self.retrieve_calls = 0

    async def get_session_context(self, session_id: str) -> dict[str, object] | None:
        self.session_calls += 1
        if session_id:
            return {
                "session_id": session_id,
                "created_at": "2026-04-21T00:00:00+00:00",
                "last_accessed": "2026-04-21T00:00:00+00:00",
                "topics": ["RAG chunking"],
                "insights": ["Chunk overlap helps boundary recall."],
                "total_queries": 1,
            }
        return None

    async def retrieve_relevant_insights(self, query: str, top_k: int = 3) -> list[dict[str, object]]:
        self.retrieve_calls += 1
        return [
            {
                "topic": "RAG chunking",
                "insight": "Chunk overlap helps boundary recall.",
                "source_count": 2,
                "created_at": "2026-04-21T00:00:00+00:00",
                "session_id": "session-1",
            }
        ]

    async def save_insight(self, topic: str, insight: str, source_count: int, session_id: str) -> None:
        self.saved.append(
            {
                "kind": "long_term",
                "topic": topic,
                "insight": insight,
                "source_count": source_count,
                "session_id": session_id,
            }
        )

    async def add_session_context(self, session_id: str, topic: str, insights: list[str]) -> None:
        self.saved.append(
            {
                "kind": "session",
                "session_id": session_id,
                "topic": topic,
                "insights": insights,
            }
        )


@pytest.mark.asyncio
async def test_multi_agent_full_path() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '{"analysis": "Evidence is coherent.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=FakeMemoryService(),
        session_id="session-1",
    )

    assert result["report"] == "# Report\n\nSummary"
    assert result["analysis"] == "Evidence is coherent."
    assert result["review_verdict"] == "approved"
    assert result["agents_involved"] == ["planner", "researcher", "analyst", "writer", "reviewer"]


@pytest.mark.asyncio
async def test_multi_agent_needs_more_research() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?", "What chunk sizes work best?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '{"analysis": "Need more evidence.", "evaluation": "needs_more", "key_findings": []}'},
        {"reply": "rag chunk size tuning"},
        {"reply": '{"analysis": "Enough evidence now.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=FakeMemoryService(),
        session_id="session-1",
    )

    assert result["iterations_used"] == 2
    assert len(result["queries"]) == 2


@pytest.mark.asyncio
async def test_multi_agent_revision() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '{"analysis": "Enough evidence.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "needs_revision", "feedback": "Add limitations."}'},
        {"reply": "# Revised Report\n\nSummary with limitations"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=FakeMemoryService(),
        session_id="session-1",
    )

    assert result["report"] == "# Revised Report\n\nSummary with limitations"
    assert [step["node"] for step in result["steps"]].count("writer") == 2


@pytest.mark.asyncio
async def test_multi_agent_max_iterations() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '# analysis not enough but capped'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=1,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=FakeMemoryService(),
        session_id="session-1",
    )

    assert result["iterations_used"] == 1
    assert result["review_verdict"] == "approved"


@pytest.mark.asyncio
async def test_multi_agent_without_memory() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '{"analysis": "Enough evidence.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]
    memory_service = FakeMemoryService()

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=memory_service,
        session_id="",
    )

    assert result["report"] == "# Report\n\nSummary"
    assert memory_service.session_calls == 0
    assert memory_service.retrieve_calls == 0
    assert memory_service.saved == []


@pytest.mark.asyncio
async def test_multi_agent_with_memory() -> None:
    llm_service = AsyncMock()
    llm_service.chat.side_effect = [
        {"reply": '{"sub_tasks": ["How does overlap affect recall?"]}'},
        {"reply": "rag chunk overlap recall"},
        {"reply": '{"analysis": "Enough evidence.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'},
        {"reply": "# Report\n\nSummary"},
        {"reply": '{"verdict": "approved", "feedback": ""}'},
    ]
    memory_service = FakeMemoryService()

    result = await run_multi_agent(
        topic="RAG chunking impact",
        max_iterations=3,
        top_k=5,
        rag_service=FakeRAGService(),
        llm_service=llm_service,
        tool_registry=FakeToolRegistry(),
        memory_service=memory_service,
        session_id="session-1",
    )

    assert result["search_result_count"] == 1
    assert memory_service.session_calls == 1
    assert memory_service.retrieve_calls == 1
    assert len(memory_service.saved) == 2

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.research.nodes import (
    make_plan_node,
    make_recall_memory_node,
    make_reflect_node,
    make_revise_report_node,
    make_save_memory_node,
)
from app.services.research.state import ResearchState


class FakeMemoryService:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []
        self.session = {
            "session_id": "session-1",
            "created_at": "2026-04-21T00:00:00+00:00",
            "last_accessed": "2026-04-21T00:00:00+00:00",
            "topics": ["RAG chunking"],
            "insights": ["Chunk overlap improves boundary recall."],
            "total_queries": 1,
        }
        self.insights = [
            {
                "topic": "RAG chunking",
                "insight": "Chunk overlap improves boundary recall.",
                "source_count": 2,
                "created_at": "2026-04-21T00:00:00+00:00",
                "session_id": "session-1",
            }
        ]

    async def get_session_context(self, session_id: str) -> dict[str, object] | None:
        if session_id == "session-1":
            return self.session
        return None

    async def retrieve_relevant_insights(self, query: str, top_k: int = 3) -> list[dict[str, object]]:
        return self.insights[:top_k]

    async def save_insight(self, topic: str, insight: str, source_count: int, session_id: str) -> None:
        self.saved.append(
            {
                "topic": topic,
                "insight": insight,
                "source_count": source_count,
                "session_id": session_id,
            }
        )

    async def add_session_context(self, session_id: str, topic: str, insights: list[str]) -> None:
        self.saved.append(
            {
                "session_id": session_id,
                "topic": topic,
                "insights": insights,
            }
        )


def build_state() -> ResearchState:
    return {
        "topic": "RAG chunking impact",
        "queries": [],
        "search_results": [
            {
                "source": "knowledge_base",
                "query": "rag chunking",
                "text_snippet": "Chunk overlap improves boundary recall.",
                "score": 0.9,
                "title": "guide.pdf",
                "url": None,
            }
        ],
        "report": "Title\n\nChunk overlap improves boundary recall and retrieval quality.",
        "steps": [],
        "iteration": 1,
        "max_iterations": 3,
        "evaluation": "",
        "top_k": 5,
        "plan": [],
        "current_step": "",
        "reflection": "",
        "session_id": "session-1",
        "prior_insights": [],
    }


@pytest.mark.asyncio
async def test_plan_node_success() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"sub_tasks": ["What chunk sizes work best?", "How does overlap affect recall?"]}'
    }
    node = make_plan_node(llm_service)

    result = await node(build_state())

    assert result["plan"] == ["What chunk sizes work best?", "How does overlap affect recall?"]
    assert result["current_step"] == "What chunk sizes work best?"


@pytest.mark.asyncio
async def test_plan_node_with_insights() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": '{"sub_tasks": ["Use prior memory"]}'}
    node = make_plan_node(llm_service)
    state = build_state()
    state["prior_insights"] = ["Chunk overlap improves boundary recall."]

    result = await node(state)

    assert result["plan"] == ["Use prior memory"]


@pytest.mark.asyncio
async def test_plan_node_parse_failure() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "not json"}
    node = make_plan_node(llm_service)
    state = build_state()

    result = await node(state)

    assert result["plan"] == ["RAG chunking impact"]
    assert result["current_step"] == "RAG chunking impact"


@pytest.mark.asyncio
async def test_reflect_node_pass() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": '{"verdict": "pass", "feedback": ""}'}
    node = make_reflect_node(llm_service)

    result = await node(build_state())

    assert result["reflection"] == "pass"


@pytest.mark.asyncio
async def test_reflect_node_revise() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"verdict": "revise", "feedback": "Add limitations and source synthesis."}'
    }
    node = make_reflect_node(llm_service)

    result = await node(build_state())

    assert result["reflection"] == "Add limitations and source synthesis."


@pytest.mark.asyncio
async def test_revise_report_node() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "Revised report with stronger structure."}
    node = make_revise_report_node(llm_service)
    state = build_state()
    state["reflection"] = "Add limitations and source synthesis."

    result = await node(state)

    assert result["report"] == "Revised report with stronger structure."


@pytest.mark.asyncio
async def test_recall_memory_node() -> None:
    memory_service = FakeMemoryService()
    node = make_recall_memory_node(memory_service)

    result = await node(build_state())

    assert result["prior_insights"] == ["Chunk overlap improves boundary recall."]


@pytest.mark.asyncio
async def test_save_memory_node() -> None:
    memory_service = FakeMemoryService()
    node = make_save_memory_node(memory_service)

    await node(build_state())

    assert len(memory_service.saved) == 2
    assert memory_service.saved[0]["topic"] == "RAG chunking impact"

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.multi_agent.roles import (
    make_analyst_node,
    make_researcher_node,
    make_reviewer_node,
    make_writer_node,
)
from app.services.multi_agent.state import MultiAgentState


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


def build_state() -> MultiAgentState:
    return {
        "topic": "RAG chunking impact",
        "queries": [],
        "search_results": [],
        "report": "",
        "steps": [],
        "plan": ["How does overlap affect recall?"],
        "current_step": "How does overlap affect recall?",
        "current_phase": "research",
        "iteration": 0,
        "max_iterations": 3,
        "top_k": 5,
        "analysis": "",
        "evaluation": "",
        "review_verdict": "",
        "review_feedback": "",
        "revision_count": 0,
        "session_id": "",
        "prior_insights": [],
    }


@pytest.mark.asyncio
async def test_researcher_node_generates_query_and_searches() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "rag chunk overlap recall"}
    node = make_researcher_node(llm_service, FakeRAGService(), FakeToolRegistry())

    result = await node(build_state())

    assert result["queries"] == ["rag chunk overlap recall"]
    assert len(result["search_results"]) == 1
    assert result["iteration"] == 1
    assert any(step["node"] == "researcher" for step in result["steps"])


@pytest.mark.asyncio
async def test_analyst_node_sufficient() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"analysis": "Evidence is coherent.", "evaluation": "sufficient", "key_findings": ["Overlap helps recall."]}'
    }
    node = make_analyst_node(llm_service)
    state = build_state()
    state["search_results"] = [
        {
            "source": "knowledge_base",
            "query": "rag chunk overlap recall",
            "text_snippet": "Chunk overlap improves boundary recall.",
            "score": 0.92,
            "title": "guide.pdf",
            "url": None,
        }
    ]

    result = await node(state)

    assert result["evaluation"] == "sufficient"
    assert result["analysis"] == "Evidence is coherent."


@pytest.mark.asyncio
async def test_analyst_node_needs_more() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"analysis": "Need more evidence.", "evaluation": "needs_more", "key_findings": []}'
    }
    node = make_analyst_node(llm_service)
    state = build_state()

    result = await node(state)

    assert result["evaluation"] == "needs_more"


@pytest.mark.asyncio
async def test_writer_node_generates_report() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {"reply": "# Report\n\nSummary"}
    node = make_writer_node(llm_service)
    state = build_state()
    state["analysis"] = "Evidence is coherent."
    state["search_results"] = [
        {
            "source": "knowledge_base",
            "query": "rag chunk overlap recall",
            "text_snippet": "Chunk overlap improves boundary recall.",
            "score": 0.92,
            "title": "guide.pdf",
            "url": None,
        }
    ]

    result = await node(state)

    assert result["report"] == "# Report\n\nSummary"


@pytest.mark.asyncio
async def test_reviewer_node_approved() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"verdict": "approved", "feedback": ""}'
    }
    node = make_reviewer_node(llm_service)
    state = build_state()
    state["report"] = "# Report\n\nSummary"

    result = await node(state)

    assert result["review_verdict"] == "approved"
    assert result["review_feedback"] == ""


@pytest.mark.asyncio
async def test_reviewer_node_needs_revision() -> None:
    llm_service = AsyncMock()
    llm_service.chat.return_value = {
        "reply": '{"verdict": "needs_revision", "feedback": "Add limitations."}'
    }
    node = make_reviewer_node(llm_service)
    state = build_state()
    state["report"] = "# Report\n\nSummary"

    result = await node(state)

    assert result["review_verdict"] == "needs_revision"
    assert result["review_feedback"] == "Add limitations."

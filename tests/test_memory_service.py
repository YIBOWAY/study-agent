from __future__ import annotations

import json

import pytest

from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_save_and_retrieve_insight(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)

    await service.save_insight(
        topic="RAG chunking",
        insight="Chunk overlap helps retain boundary context.",
        source_count=3,
        session_id="session-1",
    )

    insights = await service.retrieve_relevant_insights("chunk overlap in rag", top_k=3)

    assert len(insights) == 1
    assert insights[0]["topic"] == "RAG chunking"


@pytest.mark.asyncio
async def test_retrieve_relevant_insights(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)
    await service.save_insight(
        topic="RAG chunking",
        insight="Chunk overlap helps retrieval quality.",
        source_count=2,
        session_id="session-1",
    )
    await service.save_insight(
        topic="Agent planning",
        insight="Task decomposition improves coverage for complex research.",
        source_count=4,
        session_id="session-2",
    )

    insights = await service.retrieve_relevant_insights("planning for research tasks", top_k=2)

    assert len(insights) == 1
    assert insights[0]["topic"] == "Agent planning"


@pytest.mark.asyncio
async def test_retrieve_no_match(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)
    await service.save_insight(
        topic="RAG chunking",
        insight="Chunk overlap helps retrieval quality.",
        source_count=2,
        session_id="session-1",
    )

    insights = await service.retrieve_relevant_insights("financial forecasting", top_k=2)

    assert insights == []


@pytest.mark.asyncio
async def test_session_memory_add_and_get(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)

    await service.add_session_context(
        session_id="session-1",
        topic="RAG chunking",
        insights=["Chunk overlap helps retrieval quality."],
    )

    session = await service.get_session_context("session-1")

    assert session is not None
    assert session["session_id"] == "session-1"
    assert session["topics"] == ["RAG chunking"]
    assert session["insights"] == ["Chunk overlap helps retrieval quality."]
    assert session["total_queries"] == 1


@pytest.mark.asyncio
async def test_session_memory_clear(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)
    await service.add_session_context(
        session_id="session-1",
        topic="RAG chunking",
        insights=["Chunk overlap helps retrieval quality."],
    )

    await service.clear_session("session-1")

    session = await service.get_session_context("session-1")

    assert session is None


@pytest.mark.asyncio
async def test_long_term_persistence(tmp_path: pytest.TempPathFactory) -> None:
    data_dir = tmp_path / "memory"
    service = MemoryService(data_dir=str(data_dir), max_insights=10, session_ttl=3600)
    await service.save_insight(
        topic="RAG chunking",
        insight="Chunk overlap helps retrieval quality.",
        source_count=2,
        session_id="session-1",
    )

    new_service = MemoryService(data_dir=str(data_dir), max_insights=10, session_ttl=3600)
    insights = await new_service.get_all_insights()

    assert len(insights) == 1
    assert insights[0]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_max_insights_limit(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=2, session_ttl=3600)
    await service.save_insight(
        topic="topic-1",
        insight="insight-1",
        source_count=1,
        session_id="session-1",
    )
    await service.save_insight(
        topic="topic-2",
        insight="insight-2",
        source_count=1,
        session_id="session-1",
    )
    await service.save_insight(
        topic="topic-3",
        insight="insight-3",
        source_count=1,
        session_id="session-1",
    )

    insights = await service.get_all_insights()

    assert [item["topic"] for item in insights] == ["topic-2", "topic-3"]


@pytest.mark.asyncio
async def test_long_term_file_is_written(tmp_path: pytest.TempPathFactory) -> None:
    service = MemoryService(data_dir=str(tmp_path), max_insights=10, session_ttl=3600)

    await service.save_insight(
        topic="RAG chunking",
        insight="Chunk overlap helps retrieval quality.",
        source_count=2,
        session_id="session-1",
    )

    payload = json.loads((tmp_path / "long_term.json").read_text(encoding="utf-8"))
    assert payload[0]["topic"] == "RAG chunking"

from __future__ import annotations

import pytest
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_course.memory import (
    MemoryError,
    MemoryKind,
    MemoryNote,
    MemoryRecallPolicy,
    MemoryWritePolicy,
    Notebook,
    SessionHistoryStore,
    build_history_runnable,
    format_memory_block,
)


def test_write_and_list_notes() -> None:
    book = Notebook()
    note = book.write(
        MemoryNote(
            id="m1",
            kind=MemoryKind.PREFERENCE,
            content="Always cite source evidence.",
            tags=("citation",),
            importance=5,
        )
    )
    assert note.id == "m1"
    assert book.list_notes()[0].content.startswith("Always cite")


def test_write_policy_rejects_banned_and_low_importance() -> None:
    policy = MemoryWritePolicy(
        allowed_kinds=(MemoryKind.NOTE, MemoryKind.FACT),
        min_importance=3,
        banned_substrings=("password",),
        max_content_len=50,
    )
    book = Notebook(write_policy=policy)
    with pytest.raises(MemoryError, match="not allowed"):
        book.write(
            MemoryNote(id="x", kind=MemoryKind.SCRATCH, content="tmp", importance=5)
        )
    with pytest.raises(MemoryError, match="min_importance"):
        book.write(
            MemoryNote(id="x", kind=MemoryKind.NOTE, content="ok", importance=1)
        )
    with pytest.raises(MemoryError, match="banned"):
        book.write(
            MemoryNote(
                id="x",
                kind=MemoryKind.NOTE,
                content="user password is secret",
                importance=5,
            )
        )


def test_recall_pinned_first_and_query() -> None:
    book = Notebook()
    book.write(
        MemoryNote(
            id="n1",
            kind=MemoryKind.NOTE,
            content="temporary draft about cats",
            importance=1,
        )
    )
    book.write(
        MemoryNote(
            id="p1",
            kind=MemoryKind.PINNED,
            content="Always cite source evidence for RAG claims.",
            importance=9,
        )
    )
    book.write(
        MemoryNote(
            id="n2",
            kind=MemoryKind.FACT,
            content="Citation grounding matters for RAG evaluation.",
            tags=("rag", "citation"),
            importance=7,
        )
    )
    recalled = book.recall(
        MemoryRecallPolicy(query="citation RAG", limit=2, pinned_first=True)
    )
    assert recalled[0].id == "p1"
    assert recalled[0].pinned is True
    assert any(n.id == "n2" for n in recalled)
    block = format_memory_block(recalled)
    assert "PINNED" in block


def test_runnable_with_message_history_isolated_by_session() -> None:
    store = SessionHistoryStore()
    model = FakeListChatModel(
        responses=["first answer", "second answer", "other session"]
    )
    with pytest.warns(LangChainDeprecationWarning, match="LangGraph"):
        runnable = build_history_runnable(model, store)

    first = runnable.invoke(
        {"question": "Remember that claims need evidence."},
        config={"configurable": {"session_id": "research-a"}},
    )
    second = runnable.invoke(
        {"question": "What rule did we discuss?"},
        config={"configurable": {"session_id": "research-a"}},
    )
    runnable.invoke(
        {"question": "Fresh session"},
        config={"configurable": {"session_id": "research-b"}},
    )

    assert first.content == "first answer"
    assert second.content == "second answer"
    assert len(store.get("research-a").messages) == 4
    assert len(store.get("research-b").messages) == 2
    assert "claims need evidence" in store.get("research-a").messages[0].content

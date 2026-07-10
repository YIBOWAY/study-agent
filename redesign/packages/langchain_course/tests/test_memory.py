from __future__ import annotations

import pytest
from langchain_course.memory import (
    MemoryError,
    MemoryKind,
    MemoryNote,
    MemoryRecallPolicy,
    MemoryWritePolicy,
    Notebook,
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

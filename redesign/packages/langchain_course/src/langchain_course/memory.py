"""Part 3: offline memory notebook for the LangChain track."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory


class MemoryError(ValueError):
    """Raised when a memory write or policy is invalid."""


class MemoryKind(StrEnum):
    NOTE = "note"
    PREFERENCE = "preference"
    FACT = "fact"
    WARNING = "warning"
    PINNED = "pinned"
    SCRATCH = "scratch"


@dataclass(frozen=True, slots=True)
class MemoryNote:
    id: str
    kind: MemoryKind
    content: str
    tags: tuple[str, ...] = ()
    importance: int = 1
    pinned: bool = False

    def to_record(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "content": self.content,
            "tags": list(self.tags),
            "importance": self.importance,
            "pinned": self.pinned,
        }


@dataclass(frozen=True, slots=True)
class MemoryWritePolicy:
    allowed_kinds: tuple[MemoryKind, ...] = tuple(MemoryKind)
    min_importance: int = 1
    banned_substrings: tuple[str, ...] = ()
    max_content_len: int = 2000

    def validate(self, note: MemoryNote) -> MemoryNote:
        if note.kind not in self.allowed_kinds:
            raise MemoryError(f"kind {note.kind.value!r} not allowed by write policy")
        if note.importance < self.min_importance:
            raise MemoryError(
                f"importance {note.importance} below min_importance {self.min_importance}"
            )
        if not note.id.strip():
            raise MemoryError("memory id must be non-empty")
        if not note.content.strip():
            raise MemoryError("memory content must be non-empty")
        if len(note.content) > self.max_content_len:
            raise MemoryError(
                f"content length {len(note.content)} exceeds max_content_len "
                f"{self.max_content_len}"
            )
        lowered = note.content.lower()
        for banned in self.banned_substrings:
            if banned.lower() in lowered:
                raise MemoryError(f"content contains banned substring {banned!r}")
        return note


@dataclass(frozen=True, slots=True)
class MemoryRecallPolicy:
    query: str = ""
    allowed_kinds: tuple[MemoryKind, ...] | None = None
    limit: int = 5
    pinned_first: bool = True

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise MemoryError("recall limit must be >= 1")


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN.finditer(text)}


@dataclass
class Notebook:
    """In-memory notebook with write/recall policy (not a vector store)."""

    write_policy: MemoryWritePolicy = field(default_factory=MemoryWritePolicy)
    _notes: dict[str, MemoryNote] = field(default_factory=dict, init=False, repr=False)

    def write(self, note: MemoryNote) -> MemoryNote:
        validated = self.write_policy.validate(note)
        # PINNED kind implies pinned flag for recall ordering
        if validated.kind is MemoryKind.PINNED and not validated.pinned:
            validated = MemoryNote(
                id=validated.id,
                kind=validated.kind,
                content=validated.content,
                tags=validated.tags,
                importance=validated.importance,
                pinned=True,
            )
        self._notes[validated.id] = validated
        return validated

    def list_notes(self) -> tuple[MemoryNote, ...]:
        return tuple(self._notes[k] for k in sorted(self._notes))

    def recall(self, policy: MemoryRecallPolicy) -> tuple[MemoryNote, ...]:
        allowed = (
            set(policy.allowed_kinds)
            if policy.allowed_kinds is not None
            else set(MemoryKind)
        )
        query_tokens = _tokens(policy.query)
        scored: list[tuple[tuple[int, int, int, str], MemoryNote]] = []
        for note in self._notes.values():
            if note.kind not in allowed:
                continue
            if query_tokens:
                hay = _tokens(f"{note.content} {' '.join(note.tags)}")
                overlap = len(query_tokens & hay)
                if overlap == 0 and not note.pinned:
                    continue
                score = overlap
            else:
                score = note.importance
            pinned_rank = 0 if (policy.pinned_first and note.pinned) else 1
            # lower tuple sorts first: pinned, higher score, higher importance, id
            key = (pinned_rank, -score, -note.importance, note.id)
            scored.append((key, note))
        scored.sort(key=lambda item: item[0])
        return tuple(note for _, note in scored[: policy.limit])


def notes_to_records(notes: tuple[MemoryNote, ...] | list[MemoryNote]) -> list[dict]:
    return [note.to_record() for note in notes]


def format_memory_block(notes: tuple[MemoryNote, ...] | list[MemoryNote]) -> str:
    lines = []
    for note in notes:
        pin = "PINNED " if note.pinned else ""
        lines.append(f"- [{note.kind.value}] {pin}{note.content}")
    return "\n".join(lines)


@dataclass
class SessionHistoryStore:
    """Inspectable session store used by `RunnableWithMessageHistory`."""

    _sessions: dict[str, InMemoryChatMessageHistory] = field(default_factory=dict)

    def get(self, session_id: str) -> BaseChatMessageHistory:
        if not session_id.strip():
            raise MemoryError("session_id must be non-empty")
        return self._sessions.setdefault(session_id, InMemoryChatMessageHistory())

    def session_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._sessions))


def build_history_runnable(
    model: Runnable[Any, Any],
    store: SessionHistoryStore,
    *,
    system_prompt: str = "You are a careful research assistant.",
) -> RunnableWithMessageHistory:
    """Wrap a LangChain prompt/model Runnable with per-session chat history."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    chain = prompt | model
    return RunnableWithMessageHistory(
        chain,
        store.get,
        input_messages_key="question",
        history_messages_key="history",
    )

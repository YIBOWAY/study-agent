from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_json_value

# Latin/identifier tokens, or individual CJK characters so pure Chinese queries work.
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[一-鿿㐀-䶿豈-﫿]")


class MemoryKind(StrEnum):
    WORKING = "working"
    SESSION = "session"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PINNED = "pinned"


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: str
    kind: MemoryKind | str
    content: str
    tags: Sequence[str] = ()
    importance: float = 0.5
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("content", self.content)
        try:
            kind = MemoryKind(self.kind)
        except ValueError as exc:
            allowed_kinds = ", ".join(kind.value for kind in MemoryKind)
            raise ValueError(f"kind must be one of: {allowed_kinds}") from exc
        if (
            not isinstance(self.importance, (int, float))
            or isinstance(self.importance, bool)
            or not 0 <= self.importance <= 1
        ):
            raise ValueError("importance must be a number between 0 and 1")
        tags = _tuple_of_non_empty_strings("tags", self.tags)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "importance", float(self.importance))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class MemoryWritePolicy:
    allowed_kinds: Sequence[MemoryKind | str] = tuple(MemoryKind)
    min_importance: float = 0.0
    max_content_chars: int = 2000
    forbidden_phrases: Sequence[str] = ()

    def __post_init__(self) -> None:
        allowed_kinds = tuple(_normalize_kind(kind) for kind in self.allowed_kinds)
        if not allowed_kinds:
            raise ValueError("allowed_kinds must not be empty")
        if (
            not isinstance(self.min_importance, (int, float))
            or isinstance(self.min_importance, bool)
            or not 0 <= self.min_importance <= 1
        ):
            raise ValueError("min_importance must be a number between 0 and 1")
        if (
            not isinstance(self.max_content_chars, int)
            or isinstance(self.max_content_chars, bool)
            or self.max_content_chars <= 0
        ):
            raise ValueError("max_content_chars must be a positive integer")
        forbidden_phrases = tuple(phrase.casefold() for phrase in self.forbidden_phrases)
        if any(not phrase.strip() for phrase in forbidden_phrases):
            raise ValueError("forbidden_phrases must not contain blank values")
        object.__setattr__(self, "allowed_kinds", allowed_kinds)
        object.__setattr__(self, "min_importance", float(self.min_importance))
        object.__setattr__(self, "forbidden_phrases", forbidden_phrases)

    def validate(self, record: MemoryRecord) -> MemoryRecord:
        if record.kind not in self.allowed_kinds:
            raise ValueError(f"kind {record.kind.value!r} is not allowed")
        if record.importance < self.min_importance:
            raise ValueError("importance is below policy minimum")
        normalized_content = record.content.casefold()
        if any(phrase in normalized_content for phrase in self.forbidden_phrases):
            raise ValueError("content contains forbidden phrase")
        if len(record.content) > self.max_content_chars:
            raise ValueError("content exceeds policy maximum")
        return record


@dataclass(frozen=True, slots=True)
class MemoryRecallPolicy:
    query: str
    allowed_kinds: Sequence[MemoryKind | str] = tuple(MemoryKind)
    limit: int = 5
    pinned_first: bool = True

    def __post_init__(self) -> None:
        _require_non_empty("query", self.query)
        allowed_kinds = tuple(_normalize_kind(kind) for kind in self.allowed_kinds)
        if not allowed_kinds:
            raise ValueError("allowed_kinds must not be empty")
        if not isinstance(self.limit, int) or isinstance(self.limit, bool) or self.limit <= 0:
            raise ValueError("limit must be a positive integer")
        object.__setattr__(self, "allowed_kinds", allowed_kinds)


class MemoryEngine:
    def __init__(self, write_policy: MemoryWritePolicy | None = None) -> None:
        self._write_policy = write_policy if write_policy is not None else MemoryWritePolicy()
        self._records: list[MemoryRecord] = []

    def write(self, record: MemoryRecord) -> MemoryRecord:
        self._write_policy.validate(record)
        self._records.append(record)
        return record

    def recall(self, policy: MemoryRecallPolicy) -> tuple[MemoryRecord, ...]:
        query_tokens = set(_tokenize(policy.query))
        scored: list[tuple[int, int, int, MemoryRecord]] = []
        for index, record in enumerate(self._records):
            if record.kind not in policy.allowed_kinds:
                continue
            score = _score(record, query_tokens)
            if score <= 0:
                continue
            pinned_rank = 0 if policy.pinned_first and record.kind == MemoryKind.PINNED else 1
            scored.append((pinned_rank, -score, index, record))
        scored.sort(key=lambda item: (item[0], item[1], item[2]))
        return tuple(record for _, _, _, record in scored[: policy.limit])

    def list_records(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _freeze_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return freeze_json_value(dict(metadata))


def _normalize_kind(kind: MemoryKind | str) -> MemoryKind:
    try:
        return MemoryKind(kind)
    except ValueError as exc:
        allowed_kinds = ", ".join(kind.value for kind in MemoryKind)
        raise ValueError(f"kind must be one of: {allowed_kinds}") from exc


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or isinstance(values, Mapping):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must not contain blank values")
    return result


def _tokenize(value: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _TOKEN_PATTERN.finditer(value))


def _score(record: MemoryRecord, query_tokens: set[str]) -> int:
    record_tokens = set(_tokenize(record.content)) | {tag.casefold() for tag in record.tags}
    return sum(1 for token in query_tokens if token in record_tokens)

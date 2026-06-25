from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_json_value


class ResearchRunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _freeze_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return freeze_json_value(dict(metadata))


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must not contain blank values")
    return result


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str
    description: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("name", self.name)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class ResearchRun:
    id: str
    project_id: str
    question: str
    status: ResearchRunStatus | str = ResearchRunStatus.PLANNED
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("question", self.question)
        try:
            status = ResearchRunStatus(self.status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in ResearchRunStatus)
            raise ValueError(f"status must be one of: {allowed_statuses}") from exc
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    uri: str
    title: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("uri", self.uri)
        _require_non_empty("title", self.title)
        _require_non_empty("content", self.content)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    source_id: str
    quote: str
    summary: str = ""
    location: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("source_id", self.source_id)
        _require_non_empty("quote", self.quote)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    text: str
    evidence_ids: Sequence[str] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("text", self.text)
        object.__setattr__(
            self,
            "evidence_ids",
            _tuple_of_non_empty_strings("evidence_ids", self.evidence_ids),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Report:
    id: str
    run_id: str
    title: str
    summary: str
    claims: Sequence[Claim] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("run_id", self.run_id)
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        claims = tuple(self.claims)
        if any(not isinstance(claim, Claim) for claim in claims):
            raise ValueError("claims must contain Claim objects")
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

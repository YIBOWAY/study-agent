from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from research_core.research.entities import Source, _freeze_metadata, _require_non_empty


@dataclass(frozen=True, slots=True)
class SourceInput:
    uri: str
    title: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("uri", self.uri)
        _require_non_empty("title", self.title)
        _require_non_empty("content", self.content)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class SourceIngestor:
    def __init__(self, id_prefix: str = "source") -> None:
        _require_non_empty("id_prefix", id_prefix)
        self._id_prefix = id_prefix

    def ingest_many(self, inputs: Sequence[SourceInput]) -> tuple[Source, ...]:
        return tuple(
            Source(
                id=f"{self._id_prefix}_{index}",
                uri=source_input.uri,
                title=source_input.title,
                content=source_input.content,
                metadata=source_input.metadata,
            )
            for index, source_input in enumerate(inputs, start=1)
        )

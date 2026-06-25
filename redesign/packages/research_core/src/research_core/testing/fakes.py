from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from research_core.runtime.immutability import freeze_nested
from research_core.runtime.messages import AgentMessage


@dataclass(frozen=True, slots=True)
class FakeModelResponse:
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("content must not be empty")
        object.__setattr__(self, "metadata", freeze_nested(dict(self.metadata)))


class FakeModel:
    def __init__(self, responses: Iterable[FakeModelResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[AgentMessage]] = []

    def complete(self, messages: Sequence[AgentMessage]) -> FakeModelResponse:
        self.calls.append(list(messages))
        if not self._responses:
            raise RuntimeError("FakeModel has no scripted responses left")
        return self._responses.pop(0)

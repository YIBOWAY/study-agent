from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_nested


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class AgentMessage:
    id: str
    role: MessageRole
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        try:
            object.__setattr__(self, "role", MessageRole(self.role))
        except ValueError as exc:
            allowed_roles = ", ".join(role.value for role in MessageRole)
            raise ValueError(f"role must be one of: {allowed_roles}") from exc
        if not self.content.strip():
            raise ValueError("content must not be empty")
        object.__setattr__(self, "metadata", freeze_nested(dict(self.metadata)))

    def to_provider_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}

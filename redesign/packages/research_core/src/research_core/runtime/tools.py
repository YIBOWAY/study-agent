from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from research_core.runtime.immutability import freeze_json_value, thaw_json_value
from research_core.runtime.messages import AgentMessage, MessageRole


class UnknownToolError(KeyError):
    pass


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    name: str
    arguments: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        object.__setattr__(self, "arguments", freeze_json_value(dict(self.arguments)))


@dataclass(frozen=True, slots=True)
class ToolResult:
    call_id: str
    name: str
    content: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.call_id.strip():
            raise ValueError("call_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not isinstance(self.content, Mapping):
            raise ValueError("content must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        object.__setattr__(self, "content", freeze_json_value(dict(self.content)))
        object.__setattr__(self, "metadata", freeze_json_value(dict(self.metadata)))

    def to_message(self) -> AgentMessage:
        return AgentMessage(
            id=f"tool_{self.call_id}",
            role=MessageRole.TOOL,
            content=json.dumps(
                {
                    "name": self.name,
                    "content": thaw_json_value(self.content),
                    "metadata": thaw_json_value(self.metadata),
                },
                sort_keys=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[[Mapping[str, Any]], Mapping[str, Any]]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")


class ToolRuntime:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool {tool.name!r} already registered")
        self._tools[tool.name] = tool

    def invoke(self, call: ToolCall) -> ToolResult:
        try:
            tool = self._tools[call.name]
        except KeyError as exc:
            raise UnknownToolError(f"unknown tool {call.name!r}") from exc
        return ToolResult(
            call_id=call.id,
            name=call.name,
            content=tool.handler(thaw_json_value(call.arguments)),
        )

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

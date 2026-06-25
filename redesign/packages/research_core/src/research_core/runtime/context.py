from __future__ import annotations

from collections.abc import Sequence

from research_core.runtime.messages import AgentMessage, MessageRole


class ContextBuilder:
    """Build a simple Phase 1 context window with one reserved system message.

    `max_messages` is a latest-message teaching window. Turn-aware compression
    belongs to a later context-engine phase.
    """

    def __init__(self, max_messages: int | None = None) -> None:
        if max_messages is not None and (
            not isinstance(max_messages, int) or isinstance(max_messages, bool)
        ):
            raise ValueError("max_messages must be an integer")
        if max_messages is not None and max_messages <= 0:
            raise ValueError("max_messages must be positive")
        self._max_messages = max_messages

    def build(self, system_prompt: str, messages: Sequence[AgentMessage]) -> list[AgentMessage]:
        if not system_prompt.strip():
            raise ValueError("system_prompt must not be empty")

        caller_messages = list(messages)
        for message in caller_messages:
            if message.role == MessageRole.SYSTEM:
                raise ValueError("system messages must be supplied through system_prompt")

        if self._max_messages is not None:
            caller_messages = caller_messages[-self._max_messages :]

        return [
            AgentMessage(id="system_1", role=MessageRole.SYSTEM, content=system_prompt),
            *caller_messages,
        ]

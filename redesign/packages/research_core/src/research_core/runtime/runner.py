from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from research_core.runtime.context import ContextBuilder
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.runtime.tools import ToolCall, ToolResult, ToolRuntime, UnknownToolError


class AgentModel(Protocol):
    def complete(self, messages: Sequence[AgentMessage]) -> object: ...


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    final_message: AgentMessage
    messages: Sequence[AgentMessage]
    events: Sequence[RunEvent]

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "events", tuple(self.events))


class AgentRunner:
    def __init__(
        self,
        model: AgentModel,
        tools: ToolRuntime | None = None,
        context_builder: ContextBuilder | None = None,
        max_steps: int = 4,
    ) -> None:
        if not isinstance(max_steps, int) or isinstance(max_steps, bool):
            raise ValueError("max_steps must be an integer")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        self._model = model
        self._tools = tools if tools is not None else ToolRuntime()
        self._context_builder = context_builder if context_builder is not None else ContextBuilder()
        self._max_steps = max_steps

    def run(self, run_id: str, system_prompt: str, user_message: str) -> AgentRunResult:
        messages = [AgentMessage(id="user_1", role=MessageRole.USER, content=user_message)]
        events: list[RunEvent] = []

        for step in range(1, self._max_steps + 1):
            context = self._context_builder.build(system_prompt=system_prompt, messages=messages)
            self._append_event(
                events,
                run_id=run_id,
                type=RunEventType.MODEL_REQUEST,
                payload={"step": step, "message_ids": [message.id for message in context]},
            )
            try:
                response = self._model.complete(context)
            except Exception as exc:
                self._append_error_event(
                    events,
                    run_id=run_id,
                    step=step,
                    kind="model_error",
                    message=str(exc),
                )
                self._raise_with_events(exc, events)
            try:
                response_content = self._response_content(response)
            except ValueError as exc:
                self._append_error_event(
                    events,
                    run_id=run_id,
                    step=step,
                    kind="model_response_error",
                    message=str(exc),
                )
                self._raise_with_events(exc, events)
            self._append_event(
                events,
                run_id=run_id,
                type=RunEventType.MODEL_RESPONSE,
                payload={"step": step, "content": response_content},
            )
            assistant_message = AgentMessage(
                id=f"assistant_{step}",
                role=MessageRole.ASSISTANT,
                content=response_content,
            )
            messages.append(assistant_message)

            try:
                tool_call = self._parse_tool_call(response_content)
            except ValueError as exc:
                self._append_error_event(
                    events,
                    run_id=run_id,
                    step=step,
                    kind="malformed_tool_call",
                    message=str(exc),
                )
                self._raise_with_events(exc, events)
            if tool_call is None:
                return AgentRunResult(
                    final_message=assistant_message,
                    messages=messages,
                    events=events,
                )

            self._append_event(
                events,
                run_id=run_id,
                type=RunEventType.TOOL_CALL,
                payload={
                    "step": step,
                    "tool_call": {
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                },
            )
            try:
                tool_result = self._tools.invoke(tool_call)
            except UnknownToolError as exc:
                self._append_error_event(
                    events,
                    run_id=run_id,
                    step=step,
                    kind="unknown_tool",
                    message=str(exc),
                )
                self._raise_with_events(exc, events)
            except Exception as exc:
                self._append_error_event(
                    events,
                    run_id=run_id,
                    step=step,
                    kind="tool_error",
                    message=str(exc),
                )
                self._raise_with_events(exc, events)
            messages.append(tool_result.to_message())
            self._append_event(
                events,
                run_id=run_id,
                type=RunEventType.TOOL_RESULT,
                payload={"step": step, "tool_result": self._tool_result_payload(tool_result)},
            )

        self._append_error_event(
            events,
            run_id=run_id,
            step=self._max_steps,
            kind="max_steps_exhausted",
            message="max_steps exhausted",
        )
        self._raise_with_events(RuntimeError("max_steps exhausted"), events)

    def _append_event(
        self,
        events: list[RunEvent],
        *,
        run_id: str,
        type: RunEventType,
        payload: Mapping[str, Any],
    ) -> None:
        events.append(
            RunEvent(
                id=f"evt_{len(events) + 1}",
                run_id=run_id,
                type=type,
                payload=payload,
            )
        )

    def _append_error_event(
        self,
        events: list[RunEvent],
        *,
        run_id: str,
        step: int,
        kind: str,
        message: str,
    ) -> None:
        self._append_event(
            events,
            run_id=run_id,
            type=RunEventType.ERROR,
            payload={"step": step, "error": {"kind": kind, "message": message}},
        )

    def _raise_with_events(self, exc: Exception, events: Sequence[RunEvent]) -> None:
        exc.events = tuple(events)  # type: ignore[attr-defined]
        raise exc

    def _response_content(self, response: object) -> str:
        content = getattr(response, "content", None)
        if not isinstance(content, str):
            raise ValueError("model response content must be a string")
        if not content.strip():
            raise ValueError("model response content must not be empty")
        return content

    def _parse_tool_call(self, content: str) -> ToolCall | None:
        if not content.lstrip().startswith("{"):
            return None

        parsed = json.loads(content)
        if not isinstance(parsed, Mapping):
            return None
        if "tool_call" not in parsed:
            raise ValueError("JSON model responses must contain tool_call")

        raw_call = parsed["tool_call"]
        if not isinstance(raw_call, Mapping):
            raise ValueError("tool_call must be a mapping")
        if "arguments" not in raw_call:
            raise ValueError("tool_call arguments must be supplied")
        arguments = raw_call["arguments"]
        if not isinstance(arguments, Mapping):
            raise ValueError("tool_call arguments must be a mapping")
        call_id = raw_call.get("id", "")
        name = raw_call.get("name", "")
        if not isinstance(call_id, str):
            raise ValueError("tool_call id must be a string")
        if not isinstance(name, str):
            raise ValueError("tool_call name must be a string")
        return ToolCall(
            id=call_id,
            name=name,
            arguments=arguments,
        )

    def _tool_result_payload(self, tool_result: ToolResult) -> dict[str, Any]:
        return {
            "call_id": tool_result.call_id,
            "name": tool_result.name,
            "content": tool_result.content,
            "metadata": tool_result.metadata,
        }

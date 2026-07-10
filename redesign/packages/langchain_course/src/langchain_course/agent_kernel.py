"""Part 1: inspectable tool-calling agent loop (LangChain-native).

Uses `model.bind_tools(...)` + message history — not LangGraph, and not
`research_core.AgentRunner`. Intermediate steps are recorded so learners can
inspect think → act → observe without FakeModel.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from langchain_course.config import DeepSeekSettings
from langchain_course.deepseek import build_deepseek_chat_model


class AgentKernelError(RuntimeError):
    """Raised when the tool-calling loop cannot finish cleanly."""


@dataclass(frozen=True, slots=True)
class AgentStep:
    kind: str
    payload: dict[str, Any]


@dataclass(slots=True)
class AgentRunResult:
    final_text: str
    steps: list[AgentStep] = field(default_factory=list)
    message_records: list[dict[str, Any]] = field(default_factory=list)


def step_kinds(result: AgentRunResult) -> list[str]:
    return [step.kind for step in result.steps]


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _message_record(message: BaseMessage) -> dict[str, Any]:
    record: dict[str, Any] = {
        "type": message.type,
        "content": _content_to_text(message.content),
    }
    tool_calls = getattr(message, "tool_calls", None) or []
    if tool_calls:
        record["tool_calls"] = [
            {
                "id": tc.get("id"),
                "name": tc.get("name"),
                "args": tc.get("args") or {},
            }
            for tc in tool_calls
        ]
    tool_call_id = getattr(message, "tool_call_id", None)
    if tool_call_id:
        record["tool_call_id"] = tool_call_id
    name = getattr(message, "name", None)
    if name:
        record["name"] = name
    return record


def _tool_map(tools: Sequence[BaseTool]) -> dict[str, BaseTool]:
    return {tool.name: tool for tool in tools}


def run_tool_calling_agent(
    *,
    user_message: str,
    system_prompt: str = "You are a careful research assistant.",
    tools: Sequence[BaseTool] | None = None,
    model: BaseChatModel | None = None,
    settings: DeepSeekSettings | None = None,
    max_steps: int = 6,
) -> AgentRunResult:
    """Run a multi-step tool-calling loop and record inspectable steps.

    When `model` is None, builds a DeepSeek ChatOpenAI client from settings/env/.env.
    Unit tests should pass a fake model with `bind_tools` + `invoke`.
    """
    if max_steps < 1:
        raise AgentKernelError("max_steps must be >= 1")

    tool_list = list(tools or [])
    tools_by_name = _tool_map(tool_list)
    chat = model if model is not None else build_deepseek_chat_model(settings)
    bound = chat.bind_tools(tool_list) if tool_list else chat

    messages: list[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    steps: list[AgentStep] = [
        AgentStep(kind="user_message", payload={"content": user_message}),
    ]

    for _ in range(max_steps):
        steps.append(
            AgentStep(
                kind="model_request",
                payload={"message_count": len(messages)},
            )
        )
        ai_message = bound.invoke(messages)
        if not isinstance(ai_message, AIMessage):
            raise AgentKernelError(
                f"expected AIMessage from model, got {type(ai_message)!r}"
            )
        messages.append(ai_message)

        tool_calls = list(getattr(ai_message, "tool_calls", None) or [])
        text = _content_to_text(ai_message.content)
        steps.append(
            AgentStep(
                kind="model_response",
                payload={
                    "content": text,
                    "tool_call_count": len(tool_calls),
                    "tool_names": [tc.get("name") for tc in tool_calls],
                },
            )
        )

        if not tool_calls:
            return AgentRunResult(
                final_text=text,
                steps=steps,
                message_records=[_message_record(m) for m in messages],
            )

        for tool_call in tool_calls:
            name = tool_call.get("name") or ""
            call_id = tool_call.get("id") or name
            args = tool_call.get("args") or {}
            steps.append(
                AgentStep(
                    kind="tool_call",
                    payload={"id": call_id, "name": name, "args": dict(args)},
                )
            )
            tool = tools_by_name.get(name)
            if tool is None:
                observation = f"unknown tool: {name}"
            else:
                try:
                    observation = tool.invoke(args)
                except Exception as exc:  # noqa: BLE001 - surface tool failures
                    observation = f"tool error: {type(exc).__name__}: {exc}"
            result_text = (
                observation if isinstance(observation, str) else str(observation)
            )
            steps.append(
                AgentStep(
                    kind="tool_result",
                    payload={
                        "id": call_id,
                        "name": name,
                        "content": result_text,
                    },
                )
            )
            messages.append(
                ToolMessage(
                    content=result_text,
                    tool_call_id=call_id,
                    name=name,
                )
            )

    raise AgentKernelError(
        f"agent stopped after max_steps={max_steps} without a final text response"
    )

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_course.agent_kernel import (
    AgentKernelError,
    ToolGateDecision,
    run_tool_calling_agent,
    step_kinds,
)
from langchain_course.tools_echo import add, echo


class ScriptedChatModel:
    """Minimal stand-in for BaseChatModel used only in offline unit tests."""

    def __init__(self, responses: list[AIMessage]) -> None:
        self._responses = list(responses)
        self.bind_calls: list[list[str]] = []
        self.invoke_payloads: list[list[Any]] = []

    def bind_tools(self, tools: list[Any], **_kwargs: Any) -> ScriptedChatModel:
        self.bind_calls.append([getattr(t, "name", str(t)) for t in tools])
        return self

    def invoke(self, messages: list[Any], **_kwargs: Any) -> AIMessage:
        self.invoke_payloads.append(list(messages))
        if not self._responses:
            raise RuntimeError("ScriptedChatModel has no responses left")
        return self._responses.pop(0)


def test_plain_final_response_without_tools() -> None:
    model = ScriptedChatModel(
        [AIMessage(content="final answer")],
    )
    result = run_tool_calling_agent(
        user_message="hello",
        system_prompt="be careful",
        tools=[],
        model=model,  # type: ignore[arg-type]
    )
    assert result.final_text == "final answer"
    assert step_kinds(result) == [
        "user_message",
        "model_request",
        "model_response",
    ]
    assert model.bind_calls == []


def test_tool_calling_loop_with_echo() -> None:
    model = ScriptedChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "echo",
                        "args": {"text": "hello"},
                    }
                ],
            ),
            AIMessage(content="The tool said hello."),
        ]
    )
    result = run_tool_calling_agent(
        user_message="echo hello",
        tools=[echo],
        model=model,  # type: ignore[arg-type]
    )
    assert result.final_text == "The tool said hello."
    assert step_kinds(result) == [
        "user_message",
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]
    tool_result = next(s for s in result.steps if s.kind == "tool_result")
    assert tool_result.payload["content"] == "hello"
    assert model.bind_calls == [["echo"]]

    second_request = model.invoke_payloads[1]
    types = [type(m) for m in second_request]
    assert SystemMessage in types
    assert HumanMessage in types
    assert AIMessage in types
    assert ToolMessage in types


def test_multi_tool_add_then_final() -> None:
    model = ScriptedChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "add", "args": {"a": 2, "b": 3}},
                ],
            ),
            AIMessage(content="sum is 5"),
        ]
    )
    result = run_tool_calling_agent(
        user_message="2+3",
        tools=[add, echo],
        model=model,  # type: ignore[arg-type]
    )
    assert result.final_text == "sum is 5"
    assert "tool_call" in step_kinds(result)
    tool_result = next(s for s in result.steps if s.kind == "tool_result")
    assert tool_result.payload["content"] == "5.0" or tool_result.payload["content"] == "5"


def test_max_steps_raises() -> None:
    forever_tool = AIMessage(
        content="",
        tool_calls=[{"id": "c1", "name": "echo", "args": {"text": "x"}}],
    )
    model = ScriptedChatModel([forever_tool, forever_tool, forever_tool])
    with pytest.raises(AgentKernelError, match="max_steps"):
        run_tool_calling_agent(
            user_message="loop",
            tools=[echo],
            model=model,  # type: ignore[arg-type]
            max_steps=2,
        )


def test_unknown_tool_records_error_observation() -> None:
    model = ScriptedChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "missing", "args": {}},
                ],
            ),
            AIMessage(content="handled missing tool"),
        ]
    )
    result = run_tool_calling_agent(
        user_message="call missing",
        tools=[echo],
        model=model,  # type: ignore[arg-type]
    )
    tool_result = next(s for s in result.steps if s.kind == "tool_result")
    assert "unknown tool" in tool_result.payload["content"]
    assert result.final_text == "handled missing tool"


def test_tool_gate_blocks_before_tool_execution() -> None:
    calls: list[str] = []

    def dangerous_tool(value: str) -> str:
        """Record a dangerous side effect for the gate test."""
        calls.append(value)
        return value

    from langchain_core.tools import StructuredTool

    dangerous = StructuredTool.from_function(dangerous_tool, name="dangerous")
    model = ScriptedChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "gate_1", "name": "dangerous", "args": {"value": "boom"}}
                ],
            ),
            AIMessage(content="blocked safely"),
        ]
    )

    result = run_tool_calling_agent(
        user_message="run dangerous",
        tools=[dangerous],
        model=model,  # type: ignore[arg-type]
        before_tool=lambda _name, _args: ToolGateDecision(
            allowed=False,
            mode="deny",
            reason="requires human review",
        ),
    )

    assert calls == []
    assert "tool_decision" in step_kinds(result)
    decision = next(step for step in result.steps if step.kind == "tool_decision")
    assert decision.payload["allowed"] is False
    tool_result = next(step for step in result.steps if step.kind == "tool_result")
    assert "blocked" in tool_result.payload["content"]

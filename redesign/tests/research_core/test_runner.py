import json

from research_core.runtime import AgentRunner, AgentRunResult, UnknownToolError
from research_core.runtime.events import RunEvent
from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.runtime.tools import ToolCall, ToolDefinition, ToolResult, ToolRuntime
from research_core.testing.fakes import FakeModel, FakeModelResponse


def _event_types(result: AgentRunResult) -> list[str]:
    return [event.type.value for event in result.events]


def _exception_events(exc: Exception) -> tuple[RunEvent, ...]:
    return exc.events  # type: ignore[attr-defined]


class MetadataToolRuntime(ToolRuntime):
    def invoke(self, call: ToolCall) -> ToolResult:
        return ToolResult(
            call_id=call.id,
            name=call.name,
            content={"text": "hello"},
            metadata={"source": "unit"},
        )


class BlankContentModel:
    def complete(self, messages: list[AgentMessage]) -> object:
        return type("BlankResponse", (), {"content": " "})()


def test_agent_runner_returns_plain_text_response_as_final_message() -> None:
    model = FakeModel([FakeModelResponse(content="final answer")])

    result = AgentRunner(model=model).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.final_message == AgentMessage(
        id="assistant_1",
        role=MessageRole.ASSISTANT,
        content="final answer",
    )
    assert result.messages == (
        AgentMessage(id="user_1", role=MessageRole.USER, content="hello"),
        result.final_message,
    )
    assert _event_types(result) == ["model_request", "model_response"]
    assert [event.run_id for event in result.events] == ["run_1", "run_1"]
    assert model.calls == [
        [
            AgentMessage(id="system_1", role=MessageRole.SYSTEM, content="You are careful."),
            AgentMessage(id="user_1", role=MessageRole.USER, content="hello"),
        ]
    ]


def test_agent_runner_executes_tool_call_then_returns_final_answer() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content=(
                    '{"tool_call": {"id": "call_1", "name": "echo", '
                    '"arguments": {"text": "hello"}}}'
                )
            ),
            FakeModelResponse(content="final answer"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = AgentRunner(model=model, tools=tools).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.final_message == AgentMessage(
        id="assistant_2",
        role=MessageRole.ASSISTANT,
        content="final answer",
    )
    assert _event_types(result) == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]
    assert result.events[2].payload == {
        "step": 1,
        "tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}},
    }
    assert result.events[3].payload == {
        "step": 1,
        "tool_result": {
            "call_id": "call_1",
            "name": "echo",
            "content": {"text": "hello"},
            "metadata": {},
        },
    }
    assert json.loads(result.messages[2].content) == {
        "content": {"text": "hello"},
        "metadata": {},
        "name": "echo",
    }
    assert [message.id for message in model.calls[1]] == [
        "system_1",
        "user_1",
        "assistant_1",
        "tool_call_1",
    ]


def test_agent_runner_executes_multiple_tool_calls_before_final_answer() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content=(
                    '{"tool_call": {"id": "call_1", "name": "echo", '
                    '"arguments": {"text": "first"}}}'
                )
            ),
            FakeModelResponse(
                content=(
                    '{"tool_call": {"id": "call_2", "name": "echo", '
                    '"arguments": {"text": "second"}}}'
                )
            ),
            FakeModelResponse(content="final answer"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = AgentRunner(model=model, tools=tools, max_steps=3).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.final_message.content == "final answer"
    assert _event_types(result) == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]
    assert [message.id for message in model.calls[2]] == [
        "system_1",
        "user_1",
        "assistant_1",
        "tool_call_1",
        "assistant_2",
        "tool_call_2",
    ]


def test_agent_runner_can_finish_on_exact_max_steps_boundary() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content=(
                    '{"tool_call": {"id": "call_1", "name": "echo", '
                    '"arguments": {"text": "hello"}}}'
                )
            ),
            FakeModelResponse(content="final answer"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = AgentRunner(model=model, tools=tools, max_steps=2).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.final_message.content == "final answer"
    assert _event_types(result) == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]


def test_agent_runner_preserves_tool_result_metadata_in_events() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {}}}'
            ),
            FakeModelResponse(content="final answer"),
        ]
    )

    result = AgentRunner(model=model, tools=MetadataToolRuntime()).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert result.events[3].payload == {
        "step": 1,
        "tool_result": {
            "call_id": "call_1",
            "name": "echo",
            "content": {"text": "hello"},
            "metadata": {"source": "unit"},
        },
    }


def test_agent_runner_emits_error_event_before_raising_for_malformed_tool_call() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "arguments": {"text": "hello"}}}'
            )
        ]
    )

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "name must not be empty" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected malformed tool call to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {"kind": "malformed_tool_call", "message": "name must not be empty"},
    }


def test_agent_runner_rejects_json_without_tool_call_with_error_event() -> None:
    model = FakeModel([FakeModelResponse(content='{"message": "hello"}')])

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "JSON model responses must contain tool_call" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected JSON object without tool_call to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {
            "kind": "malformed_tool_call",
            "message": "JSON model responses must contain tool_call",
        },
    }


def test_agent_runner_rejects_tool_call_without_arguments_with_error_event() -> None:
    model = FakeModel(
        [FakeModelResponse(content='{"tool_call": {"id": "call_1", "name": "echo"}}')]
    )

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "tool_call arguments must be supplied" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected missing arguments to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {
            "kind": "malformed_tool_call",
            "message": "tool_call arguments must be supplied",
        },
    }


def test_agent_runner_emits_error_event_before_raising_for_invalid_tool_call_json() -> None:
    model = FakeModel([FakeModelResponse(content='{"tool_call":')])

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "Expecting value" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected invalid tool-call JSON to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "error",
    ]
    assert events[-1].payload["error"]["kind"] == "malformed_tool_call"


def test_agent_runner_emits_error_event_before_raising_for_tool_result_error() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "bad", "arguments": {}}}'
            )
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="bad",
            description="Return non-JSON-compatible content.",
            handler=lambda arguments: {"flags": {"cached"}},
        )
    )

    try:
        AgentRunner(model=model, tools=tools).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected tool result error to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "tool_call",
        "error",
    ]
    assert events[-1].payload["error"]["kind"] == "tool_error"


def test_agent_runner_classifies_registered_tool_key_error_as_tool_error() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "needs_key", "arguments": {}}}'
            )
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="needs_key",
            description="Raises a handler KeyError.",
            handler=lambda arguments: arguments["missing"],
        )
    )

    try:
        AgentRunner(model=model, tools=tools).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except KeyError as exc:
        assert "missing" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected registered tool handler KeyError to raise")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "tool_call",
        "error",
    ]
    assert events[-1].payload["error"]["kind"] == "tool_error"


def test_agent_runner_emits_error_event_before_raising_for_model_failure() -> None:
    model = FakeModel([])

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except RuntimeError as exc:
        assert "FakeModel has no scripted responses left" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected model failure to raise RuntimeError")

    assert [event.type.value for event in events] == ["model_request", "error"]
    assert events[-1].payload["error"]["kind"] == "model_error"


def test_agent_runner_rejects_blank_model_response_with_error_event() -> None:
    try:
        AgentRunner(model=BlankContentModel()).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "model response content must not be empty" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected blank model response to raise ValueError")

    assert [event.type.value for event in events] == ["model_request", "error"]
    assert events[-1].payload == {
        "step": 1,
        "error": {
            "kind": "model_response_error",
            "message": "model response content must not be empty",
        },
    }


def test_agent_runner_rejects_bad_model_response_with_error_event() -> None:
    class BadModel:
        def complete(self, messages: list[AgentMessage]) -> object:
            return object()

    try:
        AgentRunner(model=BadModel()).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "model response content must be a string" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected bad model response to raise ValueError")

    assert [event.type.value for event in events] == ["model_request", "error"]
    assert events[-1].payload == {
        "step": 1,
        "error": {
            "kind": "model_response_error",
            "message": "model response content must be a string",
        },
    }


def test_agent_runner_rejects_non_string_tool_call_fields_with_error_event() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": 1, "name": "echo", "arguments": {}}}'
            )
        ]
    )

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except ValueError as exc:
        assert "tool_call id must be a string" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected malformed tool call to raise ValueError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {"kind": "malformed_tool_call", "message": "tool_call id must be a string"},
    }


def test_agent_runner_emits_error_event_before_raising_for_unknown_tool() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "missing", "arguments": {}}}'
            )
        ]
    )

    try:
        AgentRunner(model=model).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except UnknownToolError as exc:
        assert "missing" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected unknown tool to raise KeyError")

    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "tool_call",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {"kind": "unknown_tool", "message": "\"unknown tool 'missing'\""},
    }


def test_agent_runner_rejects_invalid_max_steps() -> None:
    model = FakeModel([FakeModelResponse(content="final answer")])

    for max_steps in (0, -1, 1.5, True):
        try:
            AgentRunner(model=model, max_steps=max_steps)
        except ValueError as exc:
            assert "max_steps" in str(exc)
        else:
            raise AssertionError("Expected invalid max_steps to be rejected")


def test_agent_runner_raises_when_max_steps_are_exhausted() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {}}}'
            ),
            FakeModelResponse(content="would exceed budget"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo empty payload.",
            handler=lambda arguments: {},
        )
    )

    try:
        AgentRunner(model=model, tools=tools, max_steps=1).run(
            run_id="run_1",
            system_prompt="You are careful.",
            user_message="hello",
        )
    except RuntimeError as exc:
        assert "max_steps exhausted" in str(exc)
        events = _exception_events(exc)
    else:
        raise AssertionError("Expected max_steps exhaustion to raise RuntimeError")

    assert len(model.calls) == 1
    assert [event.type.value for event in events] == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "error",
    ]
    assert events[-1].payload == {
        "step": 1,
        "error": {"kind": "max_steps_exhausted", "message": "max_steps exhausted"},
    }

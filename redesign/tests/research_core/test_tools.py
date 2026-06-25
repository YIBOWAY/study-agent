import json
from dataclasses import FrozenInstanceError

from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.runtime.tools import ToolCall, ToolDefinition, ToolResult, ToolRuntime


def test_tool_call_rejects_blank_id_and_name() -> None:
    try:
        ToolCall(id=" ", name="echo", arguments={})
    except ValueError as exc:
        assert "id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank id to be rejected")

    try:
        ToolCall(id="call_1", name="", arguments={})
    except ValueError as exc:
        assert "name must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank name to be rejected")


def test_tool_call_arguments_are_copied_and_read_only() -> None:
    arguments = {"query": "initial", "filters": {"limit": 3}}
    call = ToolCall(id="call_1", name="search", arguments=arguments)

    arguments["query"] = "mutated"
    arguments["filters"]["limit"] = 10

    assert call.arguments["query"] == "initial"
    assert call.arguments["filters"]["limit"] == 3

    try:
        call.arguments["query"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected arguments to be read-only")

    try:
        call.arguments["filters"]["limit"] = 20
    except TypeError:
        pass
    else:
        raise AssertionError("Expected nested arguments to be read-only")


def test_tool_result_to_message_returns_tool_message_with_stable_json_content() -> None:
    result = ToolResult(
        call_id="call_1",
        name="search",
        content={"details": ["a", "b"], "answer": 42},
        metadata={"source": "unit"},
    )

    message = result.to_message()

    assert message == AgentMessage(
        id="tool_call_1",
        role=MessageRole.TOOL,
        content=json.dumps(
            {
                "name": "search",
                "content": {"answer": 42, "details": ["a", "b"]},
                "metadata": {"source": "unit"},
            },
            sort_keys=True,
        ),
    )


def test_tool_result_rejects_blank_call_id_and_name() -> None:
    try:
        ToolResult(call_id="", name="search", content={})
    except ValueError as exc:
        assert "call_id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank call_id to be rejected")

    try:
        ToolResult(call_id="call_1", name=" ", content={})
    except ValueError as exc:
        assert "name must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank name to be rejected")


def test_tool_result_content_and_metadata_are_copied_and_read_only() -> None:
    content = {"answer": {"text": "initial"}}
    metadata = {"usage": {"tool_calls": 1}}
    result = ToolResult(call_id="call_1", name="search", content=content, metadata=metadata)

    content["answer"]["text"] = "mutated"
    metadata["usage"]["tool_calls"] = 2

    assert result.content["answer"]["text"] == "initial"
    assert result.metadata["usage"]["tool_calls"] == 1

    try:
        result.content["answer"]["text"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected content to be read-only")

    try:
        result.metadata["usage"]["tool_calls"] = 3
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata to be read-only")


def test_tool_result_rejects_non_json_compatible_content_and_metadata() -> None:
    try:
        ToolResult(call_id="call_1", name="search", content={"flags": {"cached"}})
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible content to be rejected")

    try:
        ToolResult(call_id="call_1", name="search", content={}, metadata={"score": float("inf")})
    except ValueError as exc:
        assert "payload float values must be finite" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible metadata to be rejected")


def test_tool_result_rejects_non_mapping_content() -> None:
    try:
        ToolResult(call_id="call_1", name="search", content=["bad"])
    except ValueError as exc:
        assert "content must be a mapping" in str(exc)
    else:
        raise AssertionError("Expected non-mapping content to be rejected")


def test_tool_contracts_are_frozen_and_slotted() -> None:
    call = ToolCall(id="call_1", name="search", arguments={})
    result = ToolResult(call_id="call_1", name="search", content={})
    definition = ToolDefinition(
        name="search",
        description="Search.",
        handler=lambda arguments: {},
    )

    for contract in (call, result, definition):
        assert not hasattr(contract, "__dict__")
        try:
            contract.name = "mutated"
        except (AttributeError, FrozenInstanceError):
            pass
        else:
            raise AssertionError("Expected tool contract to be frozen")


def test_tool_definition_rejects_blank_name_and_description() -> None:
    try:
        ToolDefinition(name="", description="Echo text.", handler=lambda arguments: arguments)
    except ValueError as exc:
        assert "name must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank name to be rejected")

    try:
        ToolDefinition(name="echo", description=" ", handler=lambda arguments: arguments)
    except ValueError as exc:
        assert "description must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank description to be rejected")


def test_tool_runtime_register_rejects_duplicate_names() -> None:
    runtime = ToolRuntime()
    tool = ToolDefinition(
        name="echo",
        description="Echo text.",
        handler=lambda arguments: {"text": arguments["text"]},
    )
    runtime.register(tool)

    try:
        runtime.register(
            ToolDefinition(
                name="echo",
                description="Echo again.",
                handler=lambda arguments: {"text": arguments["text"]},
            )
        )
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Expected duplicate tool name to be rejected")


def test_tool_runtime_invokes_registered_tool() -> None:
    runtime = ToolRuntime()
    runtime.register(
        ToolDefinition(
            name="echo",
            description="Echo text.",
            handler=lambda arguments: {"text": arguments["text"]},
        )
    )

    result = runtime.invoke(ToolCall(id="call_1", name="echo", arguments={"text": "hello"}))

    assert result.call_id == "call_1"
    assert result.name == "echo"
    assert result.content["text"] == "hello"


def test_tool_runtime_invoke_raises_key_error_for_unknown_tool() -> None:
    runtime = ToolRuntime()

    try:
        runtime.invoke(ToolCall(id="call_1", name="missing", arguments={}))
    except KeyError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Expected unknown tool to raise KeyError")


def test_tool_call_rejects_non_json_compatible_arguments() -> None:
    try:
        ToolCall(id="call_1", name="echo", arguments={"flags": {"cached", "reviewed"}})
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible arguments to be rejected")


def test_tool_runtime_rejects_non_json_compatible_handler_results() -> None:
    runtime = ToolRuntime()
    runtime.register(
        ToolDefinition(
            name="bad",
            description="Return a bad payload.",
            handler=lambda arguments: {"flags": {"cached", "reviewed"}},
        )
    )

    try:
        runtime.invoke(ToolCall(id="call_1", name="bad", arguments={}))
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible handler result to be rejected")


def test_tool_runtime_list_tools_returns_registration_order_and_copy() -> None:
    runtime = ToolRuntime()
    first = ToolDefinition(name="first", description="First tool.", handler=lambda arguments: {})
    second = ToolDefinition(name="second", description="Second tool.", handler=lambda arguments: {})
    runtime.register(first)
    runtime.register(second)

    tools = runtime.list_tools()
    third = ToolDefinition(
        name="third",
        description="Third tool.",
        handler=lambda arguments: {},
    )
    tools.append(third)

    assert tools == [first, second, third]
    assert runtime.list_tools() == [first, second]

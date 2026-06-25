from research_core.runtime import ContextBuilder as RuntimeContextBuilder
from research_core.runtime.context import ContextBuilder
from research_core.runtime.messages import AgentMessage, MessageRole


def test_context_builder_inserts_system_prompt() -> None:
    builder = ContextBuilder()
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    context = builder.build(system_prompt="You are careful.", messages=messages)

    assert [message.role for message in context] == [MessageRole.SYSTEM, MessageRole.USER]
    assert context[0].content == "You are careful."


def test_context_builder_rejects_blank_system_prompt() -> None:
    builder = ContextBuilder()

    try:
        builder.build(system_prompt=" ", messages=[])
    except ValueError as exc:
        assert "system_prompt must not be empty" in str(exc)
    else:
        raise AssertionError("Expected blank system prompt to be rejected")


def test_context_builder_rejects_caller_provided_system_message() -> None:
    builder = ContextBuilder()
    messages = [
        AgentMessage(
            id="system_2",
            role=MessageRole.SYSTEM,
            content="system from caller",
        )
    ]

    try:
        builder.build(system_prompt="You are careful.", messages=messages)
    except ValueError as exc:
        assert "system messages must be supplied through system_prompt" in str(exc)
    else:
        raise AssertionError("Expected caller-provided system message to be rejected")


def test_context_builder_rejects_plain_string_system_role_message() -> None:
    builder = ContextBuilder()
    messages = [AgentMessage(id="system_2", role="system", content="system from caller")]

    try:
        builder.build(system_prompt="You are careful.", messages=messages)
    except ValueError as exc:
        assert "system messages must be supplied through system_prompt" in str(exc)
    else:
        raise AssertionError("Expected plain string system role to be rejected")


def test_context_builder_max_messages_keeps_latest_non_system_messages() -> None:
    builder = ContextBuilder(max_messages=2)
    messages = [
        AgentMessage(id="msg_1", role=MessageRole.USER, content="first"),
        AgentMessage(id="msg_2", role=MessageRole.ASSISTANT, content="second"),
        AgentMessage(id="msg_3", role=MessageRole.USER, content="third"),
    ]

    context = builder.build(system_prompt="You are careful.", messages=messages)

    assert [message.id for message in context] == ["system_1", "msg_2", "msg_3"]


def test_context_builder_rejects_non_positive_max_messages() -> None:
    for max_messages in (0, -1):
        try:
            ContextBuilder(max_messages=max_messages)
        except ValueError as exc:
            assert "max_messages must be positive" in str(exc)
        else:
            raise AssertionError("Expected non-positive max_messages to be rejected")


def test_context_builder_rejects_non_integer_max_messages() -> None:
    for max_messages in (1.5, True):
        try:
            ContextBuilder(max_messages=max_messages)
        except ValueError as exc:
            assert "max_messages must be an integer" in str(exc)
        else:
            raise AssertionError("Expected non-integer max_messages to be rejected")


def test_context_builder_returns_list_independent_from_caller_list_mutation() -> None:
    builder = ContextBuilder()
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    context = builder.build(system_prompt="You are careful.", messages=messages)
    messages.append(AgentMessage(id="msg_2", role=MessageRole.USER, content="again"))

    assert [message.id for message in context] == ["system_1", "msg_1"]


def test_context_builder_is_exported_from_runtime_package() -> None:
    assert RuntimeContextBuilder is ContextBuilder

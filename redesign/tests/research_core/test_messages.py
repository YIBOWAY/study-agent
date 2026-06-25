from research_core.runtime.messages import AgentMessage, MessageRole


def test_agent_message_requires_non_empty_id() -> None:
    try:
        AgentMessage(id=" ", role=MessageRole.USER, content="hello")
    except ValueError as exc:
        assert "id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty id to be rejected")


def test_agent_message_requires_non_empty_content() -> None:
    try:
        AgentMessage(id="msg_1", role=MessageRole.USER, content="")
    except ValueError as exc:
        assert "content must not be empty" in str(exc)
    else:
        raise AssertionError("Expected empty content to be rejected")


def test_agent_message_metadata_is_copied() -> None:
    metadata = {"source": "unit-test"}
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello", metadata=metadata)

    metadata["source"] = "mutated"

    assert message.metadata["source"] == "unit-test"


def test_agent_message_metadata_nested_values_are_copied() -> None:
    metadata = {"trace": {"step": "first"}}
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello", metadata=metadata)

    metadata["trace"]["step"] = "mutated"

    assert message.metadata["trace"]["step"] == "first"


def test_agent_message_metadata_is_read_only() -> None:
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")

    try:
        message.metadata["source"] = "unit-test"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata to be read-only")


def test_agent_message_metadata_nested_values_are_read_only() -> None:
    message = AgentMessage(
        id="msg_1",
        role=MessageRole.USER,
        content="hello",
        metadata={"trace": {"step": "first"}},
    )

    try:
        message.metadata["trace"]["step"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected nested metadata to be read-only")


def test_agent_message_to_provider_dict() -> None:
    message = AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")

    assert message.to_provider_dict() == {"role": "user", "content": "hello"}

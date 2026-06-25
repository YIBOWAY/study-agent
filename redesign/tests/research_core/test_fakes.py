from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.testing.fakes import FakeModel, FakeModelResponse


def test_fake_model_returns_scripted_response() -> None:
    model = FakeModel([FakeModelResponse(content="hello from fake")])
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    response = model.complete(messages)

    assert response.content == "hello from fake"
    assert model.calls == [messages]


def test_fake_model_returns_scripted_responses_in_order() -> None:
    model = FakeModel(
        [
            FakeModelResponse(content="first"),
            FakeModelResponse(content="second"),
        ]
    )
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    first = model.complete(messages)
    second = model.complete(messages)

    assert [first.content, second.content] == ["first", "second"]


def test_fake_model_accepts_tuple_messages() -> None:
    model = FakeModel([FakeModelResponse(content="hello from fake")])
    messages = (AgentMessage(id="msg_1", role=MessageRole.USER, content="hello"),)

    response = model.complete(messages)

    assert response.content == "hello from fake"
    assert model.calls == [list(messages)]


def test_fake_model_rejects_unexpected_call() -> None:
    model = FakeModel([])
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    try:
        model.complete(messages)
    except RuntimeError as exc:
        assert "FakeModel has no scripted responses left" in str(exc)
    else:
        raise AssertionError("Expected missing scripted response to fail")


def test_fake_model_response_can_include_metadata() -> None:
    response = FakeModelResponse(content="answer", metadata={"finish_reason": "stop"})

    assert response.metadata["finish_reason"] == "stop"


def test_fake_model_response_rejects_blank_content() -> None:
    for blank_content in ("", " "):
        try:
            FakeModelResponse(content=blank_content)
        except ValueError as exc:
            assert "content must not be empty" in str(exc)
        else:
            raise AssertionError("Expected blank content to be rejected")


def test_fake_model_response_metadata_is_copied() -> None:
    metadata = {"finish_reason": "stop"}
    response = FakeModelResponse(content="answer", metadata=metadata)

    metadata["finish_reason"] = "mutated"

    assert response.metadata["finish_reason"] == "stop"


def test_fake_model_response_metadata_nested_values_are_copied() -> None:
    metadata = {"usage": {"input_tokens": 3}}
    response = FakeModelResponse(content="answer", metadata=metadata)

    metadata["usage"]["input_tokens"] = 999

    assert response.metadata["usage"]["input_tokens"] == 3


def test_fake_model_response_metadata_is_read_only() -> None:
    response = FakeModelResponse(content="answer", metadata={"finish_reason": "stop"})

    try:
        response.metadata["finish_reason"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata to be read-only")


def test_fake_model_response_metadata_nested_values_are_read_only() -> None:
    response = FakeModelResponse(content="answer", metadata={"usage": {"input_tokens": 3}})

    try:
        response.metadata["usage"]["input_tokens"] = 999
    except TypeError:
        pass
    else:
        raise AssertionError("Expected nested metadata to be read-only")


def test_fake_model_records_copy_of_message_list() -> None:
    model = FakeModel([FakeModelResponse(content="hello from fake")])
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]

    model.complete(messages)
    messages.append(AgentMessage(id="msg_2", role=MessageRole.USER, content="again"))

    assert model.calls == [[AgentMessage(id="msg_1", role=MessageRole.USER, content="hello")]]

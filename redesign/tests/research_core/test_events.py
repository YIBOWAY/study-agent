import json

from research_core.runtime.events import RunEvent, RunEventType


def test_run_event_type_values() -> None:
    assert [event_type.value for event_type in RunEventType] == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "skill_load",
        "memory_recall",
        "memory_write",
        "delegate_start",
        "delegate_finish",
        "error",
    ]


def test_run_event_requires_non_empty_id() -> None:
    for empty_id in ("", " "):
        try:
            RunEvent(id=empty_id, run_id="run_1", type=RunEventType.MODEL_REQUEST, payload={})
        except ValueError as exc:
            assert "id must not be empty" in str(exc)
        else:
            raise AssertionError("Expected blank id to be rejected")


def test_run_event_requires_non_empty_run_id() -> None:
    for empty_run_id in ("", " "):
        try:
            RunEvent(id="evt_1", run_id=empty_run_id, type=RunEventType.MODEL_REQUEST, payload={})
        except ValueError as exc:
            assert "run_id must not be empty" in str(exc)
        else:
            raise AssertionError("Expected blank run_id to be rejected")


def test_run_event_payload_is_copied() -> None:
    payload = {"model": "fake"}
    event = RunEvent(id="evt_1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload=payload)

    payload["model"] = "mutated"

    assert event.payload["model"] == "fake"


def test_run_event_payload_is_read_only() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.MODEL_REQUEST,
        payload={"model": "fake"},
    )

    try:
        event.payload["model"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected payload to be read-only")


def test_run_event_payload_nested_mappings_are_copied() -> None:
    payload = {"trace": {"step": "first"}}
    event = RunEvent(id="evt_1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload=payload)

    payload["trace"]["step"] = "mutated"

    assert event.payload["trace"]["step"] == "first"


def test_run_event_payload_nested_mappings_are_read_only() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.MODEL_REQUEST,
        payload={"trace": {"step": "first"}},
    )

    try:
        event.payload["trace"]["step"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected nested payload mapping to be read-only")


def test_run_event_payload_standard_containers_are_copied_and_frozen() -> None:
    payload = {
        "steps": ["first"],
        "labels": ("alpha",),
    }
    event = RunEvent(id="evt_1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload=payload)

    payload["steps"].append("mutated")

    assert event.payload["steps"] == ("first",)
    assert event.payload["labels"] == ("alpha",)


def test_run_event_rejects_non_string_payload_keys() -> None:
    try:
        RunEvent(id="evt_1", run_id="run_1", type=RunEventType.MODEL_REQUEST, payload={1: "bad"})
    except ValueError as exc:
        assert "payload keys must be strings" in str(exc)
    else:
        raise AssertionError("Expected non-string payload key to be rejected")


def test_run_event_rejects_set_payload_values() -> None:
    try:
        RunEvent(
            id="evt_1",
            run_id="run_1",
            type=RunEventType.MODEL_REQUEST,
            payload={"flags": {"cached", "reviewed"}},
        )
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected set payload value to be rejected")


def test_run_event_rejects_unsupported_payload_values() -> None:
    try:
        RunEvent(
            id="evt_1",
            run_id="run_1",
            type=RunEventType.MODEL_REQUEST,
            payload={"raw": bytearray(b"bad")},
        )
    except ValueError as exc:
        assert "payload values must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected unsupported payload value to be rejected")


def test_run_event_rejects_non_finite_float_payload_values() -> None:
    for value in (float("nan"), float("inf"), float("-inf")):
        try:
            RunEvent(
                id="evt_1",
                run_id="run_1",
                type=RunEventType.MODEL_REQUEST,
                payload={"score": value},
            )
        except ValueError as exc:
            assert "payload float values must be finite" in str(exc)
        else:
            raise AssertionError("Expected non-finite float payload value to be rejected")


def test_run_event_to_record() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.TOOL_CALL,
        payload={"tool": "search"},
    )

    assert event.to_record() == {
        "id": "evt_1",
        "run_id": "run_1",
        "type": "tool_call",
        "payload": {"tool": "search"},
    }


def test_run_event_to_record_returns_plain_serializable_payload() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.TOOL_CALL,
        payload={
            "tool": "search",
            "trace": {"steps": ["request"], "labels": ("fast",)},
        },
    )

    record = event.to_record()

    assert record["payload"] == {
        "tool": "search",
        "trace": {"steps": ["request"], "labels": ["fast"]},
    }
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_run_event_to_record_returns_independent_payload() -> None:
    event = RunEvent(
        id="evt_1",
        run_id="run_1",
        type=RunEventType.TOOL_CALL,
        payload={"trace": {"steps": ["request"]}},
    )

    record = event.to_record()
    record["payload"]["trace"]["steps"].append("mutated")

    assert event.payload["trace"]["steps"] == ("request",)

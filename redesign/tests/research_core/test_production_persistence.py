import json

import pytest
from research_core.production import JSONL_EVENT_LOG_SCHEMA_VERSION, JsonlRunEventStore
from research_core.runtime.events import RunEvent, RunEventType


def _event(id: str, run_id: str, event_type: RunEventType) -> RunEvent:
    return RunEvent(
        id=id,
        run_id=run_id,
        type=event_type,
        payload={"step": 1},
    )


def test_jsonl_event_store_appends_and_reads_run_events_in_order(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    store = JsonlRunEventStore(path)

    store.append_many(
        (
            _event("evt_1", "run_1", RunEventType.MODEL_REQUEST),
            _event("evt_2", "run_1", RunEventType.MODEL_RESPONSE),
            _event("evt_3", "run_2", RunEventType.ERROR),
        )
    )

    assert [event.id for event in store.read_run("run_1")] == ["evt_1", "evt_2"]
    assert [event.id for event in store.read_run("run_2")] == ["evt_3"]
    assert store.list_run_ids() == ("run_1", "run_2")

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    first_record = json.loads(lines[0])
    assert first_record == {
        "schema_version": JSONL_EVENT_LOG_SCHEMA_VERSION,
        "event": {
            "id": "evt_1",
            "run_id": "run_1",
            "type": "model_request",
            "payload": {"step": 1},
        },
    }


def test_jsonl_event_store_creates_parent_directory_and_preserves_existing_log(
    tmp_path,
) -> None:
    path = tmp_path / "nested" / "events.jsonl"
    first_store = JsonlRunEventStore(path)
    first_store.append(_event("evt_1", "run_1", RunEventType.MODEL_REQUEST))

    second_store = JsonlRunEventStore(path)
    second_store.append(_event("evt_2", "run_1", RunEventType.MODEL_RESPONSE))

    assert [event.id for event in second_store.read_run("run_1")] == ["evt_1", "evt_2"]


def test_jsonl_event_store_rejects_invalid_records(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"schema_version": "wrong", "event": {}}\n', encoding="utf-8")
    store = JsonlRunEventStore(path)

    with pytest.raises(ValueError, match="unsupported event log schema at line 1"):
        store.read_all()


def test_jsonl_event_store_rejects_blank_run_id_and_non_events(tmp_path) -> None:
    store = JsonlRunEventStore(tmp_path / "events.jsonl")

    with pytest.raises(ValueError, match="run_id must not be empty"):
        store.read_run(" ")

    with pytest.raises(ValueError, match="event must be a RunEvent"):
        store.append(object())

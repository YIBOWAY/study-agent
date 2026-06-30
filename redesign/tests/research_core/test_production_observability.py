import json

import pytest
from research_core.production import RunDiagnostics
from research_core.runtime.events import RunEvent, RunEventType


def _event(
    id: str,
    event_type: RunEventType,
    *,
    run_id: str = "run_1",
    payload: dict[str, object] | None = None,
) -> RunEvent:
    return RunEvent(
        id=id,
        run_id=run_id,
        type=event_type,
        payload={} if payload is None else payload,
    )


def test_run_diagnostics_summarizes_event_counts_and_errors() -> None:
    diagnostics = RunDiagnostics.from_events(
        (
            _event("evt_1", RunEventType.MODEL_REQUEST, payload={"step": 1}),
            _event("evt_2", RunEventType.TOOL_CALL, payload={"step": 1}),
            _event(
                "evt_3",
                RunEventType.ERROR,
                payload={
                    "step": 1,
                    "error": {"kind": "tool_error", "message": "tool exploded"},
                },
            ),
            _event("evt_4", RunEventType.DELEGATE_EVENT, payload={"child": "run_child"}),
        )
    )

    assert diagnostics.run_id == "run_1"
    assert diagnostics.event_count == 4
    assert diagnostics.event_type_counts == {
        "model_request": 1,
        "tool_call": 1,
        "delegate_event": 1,
        "error": 1,
    }
    assert diagnostics.error_summaries == (
        {
            "event_id": "evt_3",
            "step": 1,
            "kind": "tool_error",
            "message": "tool exploded",
        },
    )
    assert diagnostics.to_record() == {
        "run_id": "run_1",
        "event_count": 4,
        "event_type_counts": {
            "model_request": 1,
            "tool_call": 1,
            "delegate_event": 1,
            "error": 1,
        },
        "error_summaries": [
            {
                "event_id": "evt_3",
                "step": 1,
                "kind": "tool_error",
                "message": "tool exploded",
            }
        ],
    }
    assert json.loads(json.dumps(diagnostics.to_record(), allow_nan=False)) == (
        diagnostics.to_record()
    )


def test_run_diagnostics_returns_independent_plain_records() -> None:
    diagnostics = RunDiagnostics.from_events(
        (
            _event(
                "evt_1",
                RunEventType.ERROR,
                payload={"error": {"kind": "model_error", "message": "boom"}},
            ),
        )
    )

    record = diagnostics.to_record()
    record["error_summaries"][0]["message"] = "mutated"

    assert diagnostics.error_summaries[0]["message"] == "boom"


def test_run_diagnostics_rejects_empty_or_mixed_run_events() -> None:
    with pytest.raises(ValueError, match="events must not be empty"):
        RunDiagnostics.from_events(())

    with pytest.raises(ValueError, match="events must belong to one run_id"):
        RunDiagnostics.from_events(
            (
                _event("evt_1", RunEventType.MODEL_REQUEST, run_id="run_1"),
                _event("evt_2", RunEventType.MODEL_RESPONSE, run_id="run_2"),
            )
        )

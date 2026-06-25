from research_core.runtime import event_type_sequence, events_to_records
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.runner import AgentRunner
from research_core.runtime.tools import ToolDefinition, ToolRuntime
from research_core.testing.fakes import FakeModel, FakeModelResponse


def test_event_type_sequence_returns_event_type_strings() -> None:
    events = [
        RunEvent(
            id="evt_1",
            run_id="run_1",
            type=RunEventType.MODEL_REQUEST,
            payload={"step": 1},
        ),
        RunEvent(
            id="evt_2",
            run_id="run_1",
            type=RunEventType.TOOL_CALL,
            payload={"step": 1},
        ),
        RunEvent(
            id="evt_3",
            run_id="run_1",
            type=RunEventType.TOOL_RESULT,
            payload={"step": 1},
        ),
    ]

    assert event_type_sequence(events) == ["model_request", "tool_call", "tool_result"]


def test_events_to_records_returns_plain_independent_event_records() -> None:
    events = [
        RunEvent(
            id="evt_1",
            run_id="run_1",
            type=RunEventType.MODEL_REQUEST,
            payload={"step": 1, "trace": {"labels": ("prompt",), "scores": [0.75]}},
        ),
        RunEvent(
            id="evt_2",
            run_id="run_1",
            type=RunEventType.MODEL_RESPONSE,
            payload={"step": 1, "content": "answer"},
        ),
    ]

    records = events_to_records(events)

    assert records == [
        {
            "id": "evt_1",
            "run_id": "run_1",
            "type": "model_request",
            "payload": {"step": 1, "trace": {"labels": ["prompt"], "scores": [0.75]}},
        },
        {
            "id": "evt_2",
            "run_id": "run_1",
            "type": "model_response",
            "payload": {"step": 1, "content": "answer"},
        },
    ]

    records[0]["payload"]["trace"]["labels"].append("mutated")
    records[0]["payload"]["trace"]["scores"].append(1.0)

    assert events[0].payload["trace"]["labels"] == ("prompt",)
    assert events[0].payload["trace"]["scores"] == (0.75,)


def test_trajectory_helpers_work_with_agent_runner_events() -> None:
    model = FakeModel(
        [
            FakeModelResponse(
                content='{"tool_call": {"id": "call_1", "name": "echo", "arguments": {}}}'
            ),
            FakeModelResponse(content="final answer"),
        ]
    )
    tools = ToolRuntime()
    tools.register(
        ToolDefinition(
            name="echo",
            description="Echo empty payload.",
            handler=lambda arguments: {"ok": True},
        )
    )
    result = AgentRunner(model=model, tools=tools).run(
        run_id="run_1",
        system_prompt="You are careful.",
        user_message="hello",
    )

    assert event_type_sequence(result.events) == [
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    ]
    assert events_to_records(result.events)[3]["payload"] == {
        "step": 1,
        "tool_result": {
            "call_id": "call_1",
            "name": "echo",
            "content": {"ok": True},
            "metadata": {},
        },
    }

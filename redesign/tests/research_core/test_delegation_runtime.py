from __future__ import annotations

import json
from collections.abc import Sequence

import pytest
from research_core.delegation import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationRuntime,
    DelegationStatus,
    DelegationTask,
)
from research_core.runtime import AgentRunResult
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.messages import AgentMessage, MessageRole


class RecordingChildRunner:
    def __init__(
        self,
        result: AgentRunResult | None = None,
        exc: Exception | None = None,
    ) -> None:
        self.result = result
        self.exc = exc
        self.calls: list[tuple[str, str, str]] = []

    def run(self, run_id: str, system_prompt: str, user_message: str) -> AgentRunResult:
        self.calls.append((run_id, system_prompt, user_message))
        if self.exc is not None:
            raise self.exc
        if self.result is None:
            raise AssertionError("RecordingChildRunner needs a result or exception")
        return self.result


def _role(**overrides: object) -> AgentRolePolicy:
    values = {
        "id": "role_reviewer",
        "name": "Reviewer",
        "system_prompt": "Review only the delegated evidence.",
        "tool_names": ("search",),
        "skill_names": ("summarize",),
        "memory_kinds": ("episodic",),
        "max_steps": 4,
    }
    values.update(overrides)
    return AgentRolePolicy(**values)


def _task(**overrides: object) -> DelegationTask:
    values = {
        "id": "task_1",
        "parent_run_id": "parent_run",
        "child_run_id": "child_run_1",
        "objective": "Summarize the delegated evidence.",
        "role": _role(),
    }
    values.update(overrides)
    return DelegationTask(**values)


def _child_event(
    id: str,
    event_type: RunEventType,
    *,
    run_id: str = "child_run_1",
    step: int = 1,
) -> RunEvent:
    return RunEvent(id=id, run_id=run_id, type=event_type, payload={"step": step})


def _agent_result(
    *,
    final_message: AgentMessage | None = None,
    events: Sequence[RunEvent] = (),
) -> AgentRunResult:
    final = final_message or AgentMessage(
        id="assistant_1",
        role=MessageRole.ASSISTANT,
        content="Child summary.",
    )
    return AgentRunResult(
        final_message=final,
        messages=(AgentMessage(id="user_1", role=MessageRole.USER, content="task"), final),
        events=events,
    )


def _event_types(events: Sequence[RunEvent]) -> list[str]:
    return [event.type.value for event in events]


def test_run_task_emits_parent_delegation_events_for_each_child_event() -> None:
    child_events = (
        _child_event("evt_child_1", RunEventType.MODEL_REQUEST),
        _child_event("evt_child_2", RunEventType.MODEL_RESPONSE),
    )
    runner = RecordingChildRunner(_agent_result(events=child_events))
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    task = _task()
    budget = DelegationBudget(
        max_child_runs=2,
        max_steps_per_child=4,
        max_total_steps=8,
    )

    result = runtime.run_task(task, budget=budget)

    assert result.status is DelegationStatus.COMPLETED
    assert _event_types(result.parent_events) == [
        "delegate_start",
        "delegate_event",
        "delegate_event",
        "delegate_finish",
    ]
    assert [event.run_id for event in result.parent_events] == [
        "parent_run",
        "parent_run",
        "parent_run",
        "parent_run",
    ]
    assert result.parent_events[0].payload == {
        "task_id": "task_1",
        "parent_run_id": "parent_run",
        "child_run_id": "child_run_1",
        "role_id": "role_reviewer",
        "tool_names": ("search",),
        "skill_names": ("summarize",),
        "memory_kinds": ("episodic",),
        "budget": {
            "max_child_runs": 2,
            "max_steps_per_child": 4,
            "max_total_steps": 8,
        },
    }
    assert result.parent_events[1].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "child_event": child_events[0].to_record(),
    }
    assert result.parent_events[2].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "child_event": child_events[1].to_record(),
    }
    assert result.parent_events[3].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "completed",
        "step_count": 1,
        "final_message": {
            "id": "assistant_1",
            "role": "assistant",
            "content": "Child summary.",
            "metadata": {},
        },
    }

    start_record = result.parent_events[0].to_record()
    assert start_record["payload"]["tool_names"] == ["search"]
    assert start_record["payload"]["skill_names"] == ["summarize"]
    assert start_record["payload"]["memory_kinds"] == ["episodic"]
    assert result.parent_events[1].to_record()["payload"]["child_event"] == (
        child_events[0].to_record()
    )
    assert json.loads(json.dumps(start_record, allow_nan=False)) == start_record
    assert json.loads(json.dumps(result.parent_events[3].to_record(), allow_nan=False)) == (
        result.parent_events[3].to_record()
    )


def test_run_task_preserves_child_final_message_and_child_events() -> None:
    final_message = AgentMessage(
        id="assistant_final",
        role=MessageRole.ASSISTANT,
        content="Preserved child answer.",
        metadata={"confidence": 0.8},
    )
    child_events = (
        _child_event("evt_child_1", RunEventType.MODEL_REQUEST),
        _child_event("evt_child_2", RunEventType.TOOL_CALL),
    )
    runner = RecordingChildRunner(
        _agent_result(final_message=final_message, events=child_events)
    )
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)

    result = runtime.run_task(_task())

    assert result.final_message == final_message
    assert result.child_events == child_events
    assert result.to_record()["final_message"] == {
        "id": "assistant_final",
        "role": "assistant",
        "content": "Preserved child answer.",
        "metadata": {"confidence": 0.8},
    }


def test_run_task_isolates_child_system_prompt_and_task_context() -> None:
    runner = RecordingChildRunner(_agent_result())
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    task = _task(
        objective="Summarize the enclosed filing.",
        context_messages=(
            AgentMessage(
                id="msg_allowed",
                role=MessageRole.USER,
                content="Allowed evidence.",
            ),
            AgentMessage(
                id="msg_prior",
                role=MessageRole.ASSISTANT,
                content="Prior delegated note.",
            ),
        ),
        metadata={"parent_history": "Parent private note that must not leak."},
    )

    runtime.run_task(task)

    assert len(runner.calls) == 1
    run_id, system_prompt, user_message = runner.calls[0]
    assert run_id == "child_run_1"
    assert system_prompt == "Review only the delegated evidence."
    assert "Objective:\nSummarize the enclosed filing." in user_message
    assert "Context Messages:" in user_message
    assert "- msg_allowed (user): Allowed evidence." in user_message
    assert "- msg_prior (assistant): Prior delegated note." in user_message
    assert "Parent private note" not in user_message


def test_run_task_returns_failed_result_and_preserves_exception_events() -> None:
    child_events = (
        _child_event("evt_child_1", RunEventType.MODEL_REQUEST),
        _child_event("evt_child_2", RunEventType.ERROR),
    )
    exc = RuntimeError("child model exploded")
    exc.events = child_events  # type: ignore[attr-defined]
    runner = RecordingChildRunner(exc=exc)
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)

    result = runtime.run_task(_task())

    assert result.status is DelegationStatus.FAILED
    assert result.error_message == "child model exploded"
    assert result.final_message is None
    assert result.child_events == child_events
    assert _event_types(result.parent_events) == [
        "delegate_start",
        "delegate_event",
        "delegate_event",
        "delegate_finish",
    ]
    assert result.parent_events[1].payload["child_event"] == child_events[0].to_record()
    assert result.parent_events[2].payload["child_event"] == child_events[1].to_record()
    assert result.parent_events[3].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "failed",
        "step_count": 1,
        "error": "child model exploded",
    }


def test_run_many_rejects_too_many_child_tasks_before_running() -> None:
    runner = RecordingChildRunner(_agent_result())
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    tasks = (
        _task(id="task_1", child_run_id="child_run_1"),
        _task(id="task_2", child_run_id="child_run_2"),
    )

    with pytest.raises(ValueError, match="max_child_runs"):
        runtime.run_many(tasks, budget=DelegationBudget(max_child_runs=1))

    assert runner.calls == []


def test_run_task_rejects_role_step_limit_over_child_budget_before_running() -> None:
    runner = RecordingChildRunner(_agent_result())
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    task = _task(role=_role(max_steps=5))

    with pytest.raises(ValueError, match="max_steps_per_child"):
        runtime.run_task(task, budget=DelegationBudget(max_steps_per_child=4))

    assert runner.calls == []


def test_run_task_returns_failed_result_when_child_exceeds_observed_step_budget() -> None:
    child_events = (
        _child_event("evt_child_1", RunEventType.MODEL_REQUEST),
        _child_event("evt_child_2", RunEventType.MODEL_REQUEST, step=2),
    )
    runner = RecordingChildRunner(_agent_result(events=child_events))
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    task = _task(role=_role(max_steps=1))

    result = runtime.run_task(task, budget=DelegationBudget(max_steps_per_child=1))

    assert result.status is DelegationStatus.FAILED
    assert "max_steps_per_child" in result.error_message
    assert result.final_message is None
    assert result.child_events == child_events
    assert _event_types(result.parent_events) == [
        "delegate_start",
        "delegate_event",
        "delegate_event",
        "delegate_finish",
    ]
    assert result.parent_events[-1].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "failed",
        "step_count": 2,
        "error": result.error_message,
    }


@pytest.mark.parametrize(
    "invalid_events",
    [
        (_child_event("evt_other", RunEventType.MODEL_REQUEST, run_id="other_child"),),
        ("not a run event",),
    ],
)
def test_run_task_ignores_invalid_exception_events_without_masking_child_failure(
    invalid_events: object,
) -> None:
    exc = RuntimeError("child model exploded")
    exc.events = invalid_events  # type: ignore[attr-defined]
    runner = RecordingChildRunner(exc=exc)
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)

    result = runtime.run_task(_task())

    assert result.status is DelegationStatus.FAILED
    assert result.error_message == "child model exploded"
    assert result.child_events == ()
    assert _event_types(result.parent_events) == ["delegate_start", "delegate_finish"]
    assert result.parent_events[-1].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "failed",
        "step_count": 0,
        "error": "child model exploded",
    }


def test_run_task_ignores_exception_events_iterables_that_raise() -> None:
    class BrokenEvents:
        def __iter__(self) -> object:
            raise RuntimeError("broken events iterator")

    exc = RuntimeError("child failed before event cleanup")
    exc.events = BrokenEvents()  # type: ignore[attr-defined]
    runner = RecordingChildRunner(exc=exc)
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)

    result = runtime.run_task(_task())

    assert result.status is DelegationStatus.FAILED
    assert result.error_message == "child failed before event cleanup"
    assert result.child_events == ()
    assert _event_types(result.parent_events) == ["delegate_start", "delegate_finish"]
    assert result.parent_events[-1].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "failed",
        "step_count": 0,
        "error": "child failed before event cleanup",
    }


def test_run_task_ignores_exception_events_properties_that_raise() -> None:
    class BrokenEventsError(RuntimeError):
        @property
        def events(self) -> object:
            raise RuntimeError("broken events property")

    exc = BrokenEventsError("child failed before events property cleanup")
    runner = RecordingChildRunner(exc=exc)
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)

    result = runtime.run_task(_task())

    assert result.status is DelegationStatus.FAILED
    assert result.error_message == "child failed before events property cleanup"
    assert result.child_events == ()
    assert _event_types(result.parent_events) == ["delegate_start", "delegate_finish"]
    assert result.parent_events[-1].payload == {
        "task_id": "task_1",
        "child_run_id": "child_run_1",
        "status": "failed",
        "step_count": 0,
        "error": "child failed before events property cleanup",
    }


def test_run_many_rejects_duplicate_task_ids_before_running() -> None:
    runner = RecordingChildRunner(_agent_result())
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    tasks = (
        _task(id="duplicate", child_run_id="child_run_1"),
        _task(id="duplicate", child_run_id="child_run_2"),
    )

    with pytest.raises(ValueError, match="duplicate task id"):
        runtime.run_many(tasks)

    assert runner.calls == []


def test_run_many_rejects_duplicate_child_run_ids_before_running() -> None:
    runner = RecordingChildRunner(_agent_result())
    runtime = DelegationRuntime(child_runner_factory=lambda role: runner)
    tasks = (
        _task(id="task_1", child_run_id="duplicate_child"),
        _task(id="task_2", child_run_id="duplicate_child"),
    )

    with pytest.raises(ValueError, match="duplicate child_run_id"):
        runtime.run_many(tasks)

    assert runner.calls == []


def test_run_many_rejects_total_child_step_budget_before_launching_next_child() -> None:
    first_runner = RecordingChildRunner(
        _agent_result(
            events=(
                _child_event("evt_child_1", RunEventType.MODEL_REQUEST, run_id="child_run_1"),
            )
        )
    )
    second_runner = RecordingChildRunner(
        _agent_result(
            events=(
                _child_event("evt_child_2", RunEventType.MODEL_REQUEST, run_id="child_run_2"),
                _child_event(
                    "evt_child_3",
                    RunEventType.MODEL_REQUEST,
                    run_id="child_run_2",
                    step=2,
                ),
            )
        )
    )
    runners = iter((first_runner, second_runner))
    runtime = DelegationRuntime(child_runner_factory=lambda role: next(runners))
    tasks = (
        _task(id="task_1", child_run_id="child_run_1", role=_role(max_steps=1)),
        _task(id="task_2", child_run_id="child_run_2", role=_role(max_steps=2)),
    )

    with pytest.raises(ValueError, match="max_total_steps"):
        runtime.run_many(
            tasks,
            budget=DelegationBudget(max_steps_per_child=2, max_total_steps=2),
        )

    assert len(first_runner.calls) == 1
    assert second_runner.calls == []

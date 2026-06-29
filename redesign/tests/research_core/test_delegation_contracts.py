import json
from dataclasses import FrozenInstanceError

import pytest
from research_core.delegation import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationMergeResult,
    DelegationResult,
    DelegationStatus,
    DelegationTask,
)
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.messages import AgentMessage, MessageRole


def _role(**overrides: object) -> AgentRolePolicy:
    values = {
        "id": "role_reviewer",
        "name": "Reviewer",
        "system_prompt": "Review the evidence carefully.",
    }
    values.update(overrides)
    return AgentRolePolicy(**values)


def _task(**overrides: object) -> DelegationTask:
    values = {
        "id": "task_1",
        "parent_run_id": "parent_run",
        "child_run_id": "child_run_1",
        "objective": "Summarize the supplied evidence.",
        "role": _role(),
    }
    values.update(overrides)
    return DelegationTask(**values)


def _child_event(id: str, event_type: RunEventType) -> RunEvent:
    return RunEvent(id=id, run_id="child_run_1", type=event_type, payload={"source": "child"})


def _parent_event(id: str, event_type: RunEventType) -> RunEvent:
    return RunEvent(id=id, run_id="parent_run", type=event_type, payload={"source": "parent"})


def test_agent_role_policy_rejects_blank_required_fields() -> None:
    for field_name in ("id", "name", "system_prompt"):
        try:
            _role(**{field_name: " "})
        except ValueError as exc:
            assert f"{field_name} must not be empty" in str(exc)
        else:
            raise AssertionError(f"Expected blank {field_name} to be rejected")


def test_agent_role_policy_rejects_blank_scope_names_and_invalid_max_steps() -> None:
    for field_name in ("tool_names", "skill_names", "memory_kinds"):
        try:
            _role(**{field_name: ["valid", " "]})
        except ValueError as exc:
            assert f"{field_name} must not contain blank values" in str(exc)
        else:
            raise AssertionError(f"Expected blank {field_name} value to be rejected")

    for invalid_max_steps in (0, -1, True):
        try:
            _role(max_steps=invalid_max_steps)
        except ValueError as exc:
            assert "max_steps must be a positive integer" in str(exc)
        else:
            raise AssertionError("Expected invalid max_steps to be rejected")


def test_agent_role_policy_rejects_scalar_and_mapping_scope_values() -> None:
    invalid_cases = [
        ("tool_names", "search"),
        ("skill_names", b"summarize"),
        ("memory_kinds", {"semantic": True}),
    ]

    for field_name, value in invalid_cases:
        try:
            _role(**{field_name: value})
        except ValueError as exc:
            assert f"{field_name} must be a sequence of strings" in str(exc)
        else:
            raise AssertionError(f"Expected scalar or mapping {field_name} to be rejected")


def test_agent_role_policy_sequences_and_metadata_are_copied_and_immutable() -> None:
    tool_names = ["search"]
    metadata = {"trace": {"owner": "parent"}}
    role = _role(tool_names=tool_names, skill_names=["summarize"], metadata=metadata)

    tool_names.append("mutated")
    metadata["trace"]["owner"] = "mutated"

    assert role.tool_names == ("search",)
    assert role.skill_names == ("summarize",)
    assert role.metadata["trace"]["owner"] == "parent"
    assert not hasattr(role, "__dict__")

    try:
        role.tool_names += ("other",)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected role tool_names to be immutable")

    try:
        role.metadata["trace"]["owner"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("Expected role metadata to be read-only")


def test_delegation_task_rejects_blank_required_fields() -> None:
    for field_name in ("id", "parent_run_id", "child_run_id", "objective"):
        try:
            _task(**{field_name: ""})
        except ValueError as exc:
            assert f"{field_name} must not be empty" in str(exc)
        else:
            raise AssertionError(f"Expected blank {field_name} to be rejected")


def test_delegation_task_rejects_system_messages_in_child_context() -> None:
    try:
        _task(
            context_messages=[
                AgentMessage(id="msg_1", role=MessageRole.SYSTEM, content="parent system prompt")
            ]
        )
    except ValueError as exc:
        assert "context_messages must not include system messages" in str(exc)
    else:
        raise AssertionError("Expected system context message to be rejected")


def test_delegation_task_rejects_non_json_compatible_context_message_metadata() -> None:
    try:
        _task(
            context_messages=[
                AgentMessage(
                    id="msg_1",
                    role=MessageRole.USER,
                    content="Use this evidence.",
                    metadata={"flags": {"cached"}},
                )
            ]
        )
    except ValueError as exc:
        assert "context_messages metadata must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible context metadata to be rejected")


def test_delegation_task_context_and_metadata_are_copied_and_immutable() -> None:
    messages = [AgentMessage(id="msg_1", role=MessageRole.USER, content="Use this evidence.")]
    metadata = {"trace": {"priority": 1}}
    task = _task(context_messages=messages, metadata=metadata)

    messages.append(AgentMessage(id="msg_2", role=MessageRole.USER, content="Mutated."))
    metadata["trace"]["priority"] = 9

    assert task.context_messages == (
        AgentMessage(id="msg_1", role=MessageRole.USER, content="Use this evidence."),
    )
    assert task.metadata["trace"]["priority"] == 1
    assert not hasattr(task, "__dict__")

    try:
        task.context_messages += (
            AgentMessage(id="msg_3", role=MessageRole.USER, content="Other."),
        )
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected task context_messages to be immutable")

    try:
        task.metadata["trace"]["priority"] = 10
    except TypeError:
        pass
    else:
        raise AssertionError("Expected task metadata to be read-only")


def test_delegation_budget_rejects_invalid_limits() -> None:
    invalid_cases = [
        {"max_child_runs": 0},
        {"max_child_runs": True},
        {"max_steps_per_child": 0},
        {"max_steps_per_child": False},
        {"max_total_steps": 0},
        {"max_total_steps": -1},
    ]

    for overrides in invalid_cases:
        try:
            DelegationBudget(**overrides)
        except ValueError as exc:
            assert "must be a positive integer" in str(exc)
        else:
            raise AssertionError(f"Expected invalid budget {overrides} to be rejected")


def test_delegation_result_rejects_events_from_unrelated_runs() -> None:
    task = _task()

    try:
        DelegationResult(
            task=task,
            status=DelegationStatus.COMPLETED,
            child_events=[
                RunEvent(
                    id="evt_child",
                    run_id="other_child",
                    type=RunEventType.MODEL_REQUEST,
                    payload={},
                )
            ],
        )
    except ValueError as exc:
        assert "child_events run_id must match task child_run_id" in str(exc)
    else:
        raise AssertionError("Expected unrelated child event run_id to be rejected")

    try:
        DelegationResult(
            task=task,
            status=DelegationStatus.COMPLETED,
            parent_events=[
                RunEvent(
                    id="evt_parent",
                    run_id="other_parent",
                    type=RunEventType.DELEGATE_FINISH,
                    payload={},
                )
            ],
        )
    except ValueError as exc:
        assert "parent_events run_id must match task parent_run_id" in str(exc)
    else:
        raise AssertionError("Expected unrelated parent event run_id to be rejected")


def test_delegation_result_rejects_non_json_compatible_final_message_metadata() -> None:
    try:
        DelegationResult(
            task=_task(),
            status=DelegationStatus.COMPLETED,
            final_message=AgentMessage(
                id="msg_final",
                role=MessageRole.ASSISTANT,
                content="Child summary.",
                metadata={"flags": {"cached"}},
            ),
        )
    except ValueError as exc:
        assert "final_message metadata must be JSON-compatible" in str(exc)
    else:
        raise AssertionError("Expected non-JSON-compatible final metadata to be rejected")


def test_delegation_result_counts_child_model_request_steps_and_records_plain_payload() -> None:
    child_events = [
        _child_event("evt_1", RunEventType.MODEL_REQUEST),
        _child_event("evt_2", RunEventType.TOOL_CALL),
        _child_event("evt_3", RunEventType.MODEL_REQUEST),
    ]
    result = DelegationResult(
        task=_task(),
        status="completed",
        final_message=AgentMessage(
            id="msg_final",
            role=MessageRole.ASSISTANT,
            content="Child summary.",
            metadata={"usage": {"tokens": 10}},
        ),
        child_events=child_events,
        parent_events=[_parent_event("evt_parent", RunEventType.DELEGATE_FINISH)],
        metadata={"labels": ["accepted"]},
    )

    child_events.append(_child_event("evt_4", RunEventType.MODEL_REQUEST))

    assert result.status is DelegationStatus.COMPLETED
    assert result.step_count == 2
    assert result.metadata["labels"] == ("accepted",)

    record = result.to_record()

    assert record["status"] == "completed"
    assert record["step_count"] == 2
    assert record["final_message"] == {
        "id": "msg_final",
        "role": "assistant",
        "content": "Child summary.",
        "metadata": {"usage": {"tokens": 10}},
    }
    assert record["child_events"][0]["type"] == "model_request"
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_delegation_merge_result_exposes_planned_and_running_results_as_unresolved() -> None:
    completed = DelegationResult(
        task=_task(id="task_completed", child_run_id="child_run_completed"),
        status=DelegationStatus.COMPLETED,
    )
    planned = DelegationResult(
        task=_task(id="task_planned", child_run_id="child_run_planned"),
        status=DelegationStatus.PLANNED,
    )
    running = DelegationResult(
        task=_task(id="task_running", child_run_id="child_run_running"),
        status=DelegationStatus.RUNNING,
    )

    merge = DelegationMergeResult.from_results(
        [completed, planned, running],
        summary="Incomplete children need parent review.",
    )

    assert [result.task.id for result in merge.unresolved_conflicts] == [
        "task_planned",
        "task_running",
    ]


def test_delegation_merge_result_preserves_task_order_and_exposes_failed_conflicts() -> None:
    first_task = _task(id="task_1", child_run_id="child_run_1")
    second_task = _task(id="task_2", child_run_id="child_run_2")
    third_task = _task(id="task_3", child_run_id="child_run_3")
    completed = DelegationResult(task=first_task, status=DelegationStatus.COMPLETED)
    failed = DelegationResult(
        task=second_task,
        status=DelegationStatus.FAILED,
        error_message="child failed",
    )
    cancelled = DelegationResult(task=third_task, status=DelegationStatus.CANCELLED)

    merge = DelegationMergeResult.from_results(
        [completed, failed, cancelled],
        summary="One child completed; two need parent review.",
    )

    assert [result.task.id for result in merge.decisions] == ["task_1", "task_2", "task_3"]
    assert [result.task.id for result in merge.unresolved_conflicts] == ["task_2", "task_3"]

    record = merge.to_record()

    assert [result["task"]["id"] for result in record["decisions"]] == [
        "task_1",
        "task_2",
        "task_3",
    ]
    assert [result["task"]["id"] for result in record["unresolved_conflicts"]] == [
        "task_2",
        "task_3",
    ]
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_delegation_merge_result_rejects_completed_explicit_conflicts() -> None:
    completed = DelegationResult(
        task=_task(id="task_completed", child_run_id="child_run_completed"),
        status=DelegationStatus.COMPLETED,
    )

    with pytest.raises(
        ValueError,
        match="unresolved_conflicts must not contain completed results",
    ):
        DelegationMergeResult(
            decisions=[completed],
            summary="A completed child is already resolved.",
            unresolved_conflicts=[completed],
        )


def test_delegation_merge_result_rejects_conflicts_outside_decisions() -> None:
    failed = DelegationResult(
        task=_task(id="task_failed", child_run_id="child_run_failed"),
        status=DelegationStatus.FAILED,
        error_message="child failed",
    )
    unrelated = DelegationResult(
        task=_task(id="task_unrelated", child_run_id="child_run_unrelated"),
        status=DelegationStatus.FAILED,
        error_message="unrelated child failed",
    )

    with pytest.raises(
        ValueError,
        match="unresolved_conflicts must be drawn from decisions",
    ):
        DelegationMergeResult(
            decisions=[failed],
            summary="Only failed decisions from this merge may stay unresolved.",
            unresolved_conflicts=[unrelated],
        )

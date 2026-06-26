import json

import pytest
from research_core.delegation import A2AAdapterStub, A2AEnvelope, AgentRolePolicy, DelegationTask
from research_core.runtime.messages import AgentMessage, MessageRole


def _role(**overrides: object) -> AgentRolePolicy:
    values = {
        "id": "role_reviewer",
        "name": "Reviewer",
        "system_prompt": "Review only the delegated evidence.",
        "tool_names": ("search", "quote"),
        "skill_names": ("summarize",),
        "memory_kinds": ("episodic", "semantic"),
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
        "context_messages": (
            AgentMessage(
                id="msg_evidence_1",
                role=MessageRole.USER,
                content="Allowed evidence one.",
            ),
            AgentMessage(
                id="msg_evidence_2",
                role=MessageRole.ASSISTANT,
                content="Allowed prior child note.",
            ),
        ),
        "metadata": {"trace": {"parent": "parent_run"}, "priority": 2},
    }
    values.update(overrides)
    return DelegationTask(**values)


def test_a2a_envelope_serializes_task_scope_context_ids_and_metadata() -> None:
    envelope = A2AEnvelope(
        task_id="task_1",
        parent_run_id="parent_run",
        child_run_id="child_run_1",
        role_id="role_reviewer",
        role_name="Reviewer",
        objective="Summarize the delegated evidence.",
        tool_names=("search", "quote"),
        skill_names=("summarize",),
        memory_kinds=("episodic", "semantic"),
        context_message_ids=("msg_evidence_1", "msg_evidence_2"),
        metadata={"trace": {"parent": "parent_run"}, "priority": 2},
    )

    record = envelope.to_record()

    assert record == {
        "schema_version": "phase4.a2a_task_delegation.v1",
        "message_type": "task_delegation",
        "task_id": "task_1",
        "parent_run_id": "parent_run",
        "child_run_id": "child_run_1",
        "role_id": "role_reviewer",
        "role_name": "Reviewer",
        "objective": "Summarize the delegated evidence.",
        "tool_names": ["search", "quote"],
        "skill_names": ["summarize"],
        "memory_kinds": ["episodic", "semantic"],
        "context_message_ids": ["msg_evidence_1", "msg_evidence_2"],
        "metadata": {"trace": {"parent": "parent_run"}, "priority": 2},
    }
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_a2a_envelope_rejects_duplicate_context_message_ids() -> None:
    with pytest.raises(
        ValueError,
        match="context_message_ids must not contain duplicate IDs",
    ):
        A2AEnvelope(
            task_id="task_1",
            parent_run_id="parent_run",
            child_run_id="child_run_1",
            role_id="role_reviewer",
            role_name="Reviewer",
            objective="Summarize the delegated evidence.",
            context_message_ids=("msg_evidence_1", "msg_evidence_1"),
        )


def test_a2a_envelope_rejects_blank_required_fields_and_invalid_sequences() -> None:
    required_field_cases = [
        {"task_id": ""},
        {"parent_run_id": " "},
        {"child_run_id": ""},
        {"role_id": ""},
        {"role_name": ""},
        {"objective": ""},
    ]

    for overrides in required_field_cases:
        values = {
            "task_id": "task_1",
            "parent_run_id": "parent_run",
            "child_run_id": "child_run_1",
            "role_id": "role_reviewer",
            "role_name": "Reviewer",
            "objective": "Summarize the delegated evidence.",
        }
        values.update(overrides)
        with pytest.raises(ValueError, match="must not be empty"):
            A2AEnvelope(**values)

    invalid_sequence_cases = [
        {"tool_names": "search"},
        {"skill_names": ("summarize", "")},
        {"memory_kinds": {"episodic": True}},
        {"context_message_ids": ("msg_1", " ")},
    ]

    for overrides in invalid_sequence_cases:
        values = {
            "task_id": "task_1",
            "parent_run_id": "parent_run",
            "child_run_id": "child_run_1",
            "role_id": "role_reviewer",
            "role_name": "Reviewer",
            "objective": "Summarize the delegated evidence.",
        }
        values.update(overrides)
        with pytest.raises(ValueError):
            A2AEnvelope(**values)


def test_a2a_adapter_stub_exports_task_as_deterministic_envelope() -> None:
    task = _task()
    adapter = A2AAdapterStub()

    first = adapter.export_task(task)
    second = adapter.export_task(task)

    assert first == second
    assert first == A2AEnvelope(
        task_id="task_1",
        parent_run_id="parent_run",
        child_run_id="child_run_1",
        role_id="role_reviewer",
        role_name="Reviewer",
        objective="Summarize the delegated evidence.",
        tool_names=("search", "quote"),
        skill_names=("summarize",),
        memory_kinds=("episodic", "semantic"),
        context_message_ids=("msg_evidence_1", "msg_evidence_2"),
    )
    assert first.to_record()["context_message_ids"] == [
        "msg_evidence_1",
        "msg_evidence_2",
    ]
    assert first.to_record()["metadata"] == {}


def test_a2a_adapter_stub_omits_private_parent_metadata_from_export_record() -> None:
    task = _task(
        metadata={
            "private_parent_history": "Do not disclose parent-only reasoning.",
            "parent_history": ["Internal parent summary."],
            "trace": {"parent": "parent_run"},
        }
    )

    record = A2AAdapterStub().export_task(task).to_record()

    serialized = json.dumps(record, sort_keys=True)
    assert record["metadata"] == {}
    assert "private_parent_history" not in serialized
    assert "parent_history" not in serialized


def test_a2a_adapter_stub_rejects_duplicate_context_message_ids() -> None:
    task = _task(
        context_messages=(
            AgentMessage(
                id="msg_duplicate",
                role=MessageRole.USER,
                content="Allowed evidence one.",
            ),
            AgentMessage(
                id="msg_duplicate",
                role=MessageRole.ASSISTANT,
                content="Allowed prior child note.",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="context_message_ids must not contain duplicate IDs",
    ):
        A2AAdapterStub().export_task(task)


def test_a2a_adapter_stub_send_rejects_transport_attempts() -> None:
    envelope = A2AAdapterStub().export_task(_task())

    with pytest.raises(NotImplementedError, match="A2A transport is not implemented"):
        A2AAdapterStub().send(envelope)

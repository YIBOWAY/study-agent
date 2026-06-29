from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, NoReturn

from research_core.delegation.contracts import DelegationTask
from research_core.runtime.immutability import freeze_json_value, thaw_json_value

A2A_SCHEMA_VERSION = "phase4.a2a_task_delegation.v1"
A2A_MESSAGE_TYPE = "task_delegation"


@dataclass(frozen=True, slots=True)
class A2AEnvelope:
    task_id: str
    parent_run_id: str
    child_run_id: str
    role_id: str
    role_name: str
    objective: str
    tool_names: Sequence[str] = ()
    skill_names: Sequence[str] = ()
    memory_kinds: Sequence[str] = ()
    context_message_ids: Sequence[str] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=A2A_SCHEMA_VERSION, init=False)
    message_type: str = field(default=A2A_MESSAGE_TYPE, init=False)

    def __post_init__(self) -> None:
        _require_non_empty("task_id", self.task_id)
        _require_non_empty("parent_run_id", self.parent_run_id)
        _require_non_empty("child_run_id", self.child_run_id)
        _require_non_empty("role_id", self.role_id)
        _require_non_empty("role_name", self.role_name)
        _require_non_empty("objective", self.objective)
        object.__setattr__(
            self,
            "tool_names",
            _tuple_of_non_empty_strings("tool_names", self.tool_names),
        )
        object.__setattr__(
            self,
            "skill_names",
            _tuple_of_non_empty_strings("skill_names", self.skill_names),
        )
        object.__setattr__(
            self,
            "memory_kinds",
            _tuple_of_non_empty_strings("memory_kinds", self.memory_kinds),
        )
        object.__setattr__(
            self,
            "context_message_ids",
            _tuple_of_unique_non_empty_strings(
                "context_message_ids",
                self.context_message_ids,
            ),
        )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "message_type": self.message_type,
            "task_id": self.task_id,
            "parent_run_id": self.parent_run_id,
            "child_run_id": self.child_run_id,
            "role_id": self.role_id,
            "role_name": self.role_name,
            "objective": self.objective,
            "tool_names": list(self.tool_names),
            "skill_names": list(self.skill_names),
            "memory_kinds": list(self.memory_kinds),
            "context_message_ids": list(self.context_message_ids),
            "metadata": thaw_json_value(self.metadata),
        }


class A2AAdapterStub:
    def export_task(self, task: DelegationTask) -> A2AEnvelope:
        # Task metadata can contain parent-only trace or private history; the stub
        # exports only the explicit child scope until a real transport policy exists.
        return A2AEnvelope(
            task_id=task.id,
            parent_run_id=task.parent_run_id,
            child_run_id=task.child_run_id,
            role_id=task.role.id,
            role_name=task.role.name,
            objective=task.objective,
            tool_names=task.role.tool_names,
            skill_names=task.role.skill_names,
            memory_kinds=task.role.memory_kinds,
            context_message_ids=tuple(message.id for message in task.context_messages),
        )

    def send(self, envelope: A2AEnvelope) -> NoReturn:
        raise NotImplementedError("A2A transport is not implemented")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or isinstance(values, Mapping):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must not contain blank values")
    return result


def _tuple_of_unique_non_empty_strings(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    result = _tuple_of_non_empty_strings(name, values)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicate IDs")
    return result


def _freeze_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return freeze_json_value(dict(metadata))

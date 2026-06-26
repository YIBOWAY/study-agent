from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.immutability import freeze_json_value, thaw_json_value
from research_core.runtime.messages import AgentMessage, MessageRole


class DelegationStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class AgentRolePolicy:
    id: str
    name: str
    system_prompt: str
    tool_names: Sequence[str] = ()
    skill_names: Sequence[str] = ()
    memory_kinds: Sequence[str] = ()
    max_steps: int = 4
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("name", self.name)
        _require_non_empty("system_prompt", self.system_prompt)
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
        _require_positive_int("max_steps", self.max_steps)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tool_names": list(self.tool_names),
            "skill_names": list(self.skill_names),
            "memory_kinds": list(self.memory_kinds),
            "max_steps": self.max_steps,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class DelegationTask:
    id: str
    parent_run_id: str
    child_run_id: str
    objective: str
    role: AgentRolePolicy
    context_messages: Sequence[AgentMessage] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("parent_run_id", self.parent_run_id)
        _require_non_empty("child_run_id", self.child_run_id)
        _require_non_empty("objective", self.objective)
        if not isinstance(self.role, AgentRolePolicy):
            raise ValueError("role must be an AgentRolePolicy")
        context_messages = tuple(self.context_messages)
        if any(not isinstance(message, AgentMessage) for message in context_messages):
            raise ValueError("context_messages must contain AgentMessage objects")
        if any(message.role == MessageRole.SYSTEM for message in context_messages):
            raise ValueError("context_messages must not include system messages")
        for message in context_messages:
            _validate_message_metadata("context_messages", message)
        object.__setattr__(self, "context_messages", context_messages)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_run_id": self.parent_run_id,
            "child_run_id": self.child_run_id,
            "objective": self.objective,
            "role": self.role.to_record(),
            "context_messages": [
                _message_to_record(message) for message in self.context_messages
            ],
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class DelegationBudget:
    max_child_runs: int = 4
    max_steps_per_child: int = 4
    max_total_steps: int = 16

    def __post_init__(self) -> None:
        _require_positive_int("max_child_runs", self.max_child_runs)
        _require_positive_int("max_steps_per_child", self.max_steps_per_child)
        _require_positive_int("max_total_steps", self.max_total_steps)

    def to_record(self) -> dict[str, int]:
        return {
            "max_child_runs": self.max_child_runs,
            "max_steps_per_child": self.max_steps_per_child,
            "max_total_steps": self.max_total_steps,
        }


@dataclass(frozen=True, slots=True)
class DelegationResult:
    task: DelegationTask
    status: DelegationStatus | str
    final_message: AgentMessage | None = None
    child_events: Sequence[RunEvent] = ()
    parent_events: Sequence[RunEvent] = ()
    error_message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.task, DelegationTask):
            raise ValueError("task must be a DelegationTask")
        try:
            status = DelegationStatus(self.status)
        except ValueError as exc:
            allowed_statuses = ", ".join(status.value for status in DelegationStatus)
            raise ValueError(f"status must be one of: {allowed_statuses}") from exc
        if self.final_message is not None and not isinstance(self.final_message, AgentMessage):
            raise ValueError("final_message must be an AgentMessage")
        if self.final_message is not None:
            _validate_message_metadata("final_message", self.final_message)
        child_events = _tuple_of_events("child_events", self.child_events)
        parent_events = _tuple_of_events("parent_events", self.parent_events)
        if any(event.run_id != self.task.child_run_id for event in child_events):
            raise ValueError("child_events run_id must match task child_run_id")
        if any(event.run_id != self.task.parent_run_id for event in parent_events):
            raise ValueError("parent_events run_id must match task parent_run_id")
        if not isinstance(self.error_message, str):
            raise ValueError("error_message must be a string")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "child_events", child_events)
        object.__setattr__(self, "parent_events", parent_events)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def step_count(self) -> int:
        return sum(1 for event in self.child_events if event.type == RunEventType.MODEL_REQUEST)

    def to_record(self) -> dict[str, Any]:
        final_message = (
            None if self.final_message is None else _message_to_record(self.final_message)
        )
        return {
            "task": self.task.to_record(),
            "status": self.status.value,
            "final_message": final_message,
            "child_events": [event.to_record() for event in self.child_events],
            "parent_events": [event.to_record() for event in self.parent_events],
            "error_message": self.error_message,
            "step_count": self.step_count,
            "metadata": thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class DelegationMergeResult:
    decisions: Sequence[DelegationResult]
    summary: str
    unresolved_conflicts: Sequence[DelegationResult] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        decisions = _tuple_of_results("decisions", self.decisions)
        _require_non_empty("summary", self.summary)
        if self.unresolved_conflicts is None:
            unresolved_conflicts = tuple(
                result
                for result in decisions
                if result.status is not DelegationStatus.COMPLETED
            )
        else:
            unresolved_conflicts = _tuple_of_results(
                "unresolved_conflicts",
                self.unresolved_conflicts,
            )
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(self, "unresolved_conflicts", unresolved_conflicts)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @classmethod
    def from_results(
        cls,
        results: Sequence[DelegationResult],
        summary: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> DelegationMergeResult:
        return cls(
            decisions=results,
            summary=summary,
            metadata={} if metadata is None else metadata,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "decisions": [result.to_record() for result in self.decisions],
            "summary": self.summary,
            "unresolved_conflicts": [
                result.to_record() for result in self.unresolved_conflicts
            ],
            "metadata": thaw_json_value(self.metadata),
        }


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _freeze_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return freeze_json_value(dict(metadata))


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or isinstance(values, Mapping):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must not contain blank values")
    return result


def _tuple_of_events(name: str, values: Sequence[RunEvent]) -> tuple[RunEvent, ...]:
    result = tuple(values)
    if any(not isinstance(event, RunEvent) for event in result):
        raise ValueError(f"{name} must contain RunEvent objects")
    return result


def _tuple_of_results(
    name: str,
    values: Sequence[DelegationResult],
) -> tuple[DelegationResult, ...]:
    result = tuple(values)
    if any(not isinstance(result_item, DelegationResult) for result_item in result):
        raise ValueError(f"{name} must contain DelegationResult objects")
    return result


def _message_to_record(message: AgentMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role.value,
        "content": message.content,
        "metadata": thaw_json_value(freeze_json_value(dict(message.metadata))),
    }


def _validate_message_metadata(name: str, message: AgentMessage) -> None:
    try:
        freeze_json_value(dict(message.metadata))
    except ValueError as exc:
        raise ValueError(f"{name} metadata must be JSON-compatible") from exc

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from research_core.delegation.contracts import (
    AgentRolePolicy,
    DelegationBudget,
    DelegationResult,
    DelegationStatus,
    DelegationTask,
)
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.immutability import freeze_json_value, thaw_json_value
from research_core.runtime.messages import AgentMessage
from research_core.runtime.runner import AgentRunResult


class ChildRunner(Protocol):
    def run(self, run_id: str, system_prompt: str, user_message: str) -> AgentRunResult: ...


ChildRunnerFactory = Callable[[AgentRolePolicy], ChildRunner]

DEFAULT_DELEGATION_BUDGET = DelegationBudget()


def filter_tools_for_role(role: AgentRolePolicy, tool_names: Sequence[str]) -> tuple[str, ...]:
    """Return tool names allowed by the role policy.

    Empty ``role.tool_names`` means "no tools allowed". Call this (or an equivalent
    check) inside every ``child_runner_factory`` before registering tools. Role
    ``skill_names`` and ``memory_kinds`` remain declarative labels until a later
    phase wires SkillRuntime / MemoryEngine into the child factory.
    """
    if not isinstance(role, AgentRolePolicy):
        raise ValueError("role must be an AgentRolePolicy")
    if isinstance(tool_names, (str, bytes)) or not isinstance(tool_names, Sequence):
        raise ValueError("tool_names must be a sequence of strings")
    requested = tuple(tool_names)
    if any(not isinstance(name, str) or not name.strip() for name in requested):
        raise ValueError("tool_names must not contain blank values")
    allowed = set(role.tool_names)
    denied = [name for name in requested if name not in allowed]
    if denied:
        denied_list = ", ".join(repr(name) for name in denied)
        raise ValueError(
            f"role {role.id!r} does not allow tools: {denied_list}; "
            f"allowed={list(role.tool_names)!r}"
        )
    return requested



class DelegationRuntime:
    def __init__(self, child_runner_factory: ChildRunnerFactory) -> None:
        self._child_runner_factory = child_runner_factory

    def run_task(
        self,
        task: DelegationTask,
        budget: DelegationBudget = DEFAULT_DELEGATION_BUDGET,
    ) -> DelegationResult:
        _validate_task_budget(task, budget)
        parent_events: list[RunEvent] = [
            _parent_event(
                task=task,
                index=1,
                event_type=RunEventType.DELEGATE_START,
                payload=_delegate_start_payload(task, budget),
            )
        ]

        try:
            runner = self._child_runner_factory(task.role)
            child_result = runner.run(
                run_id=task.child_run_id,
                system_prompt=task.role.system_prompt,
                user_message=compile_child_prompt(task),
            )
        except Exception as exc:
            child_events = _exception_events(exc, task=task)
            parent_events.extend(_delegate_event_events(task, child_events, len(parent_events)))
            step_count = _step_count(child_events)
            budget_error = _observed_step_budget_error(task, budget, step_count)
            error_message = str(exc) if not budget_error else f"{str(exc)}; {budget_error}"
            parent_events.append(
                _parent_event(
                    task=task,
                    index=len(parent_events) + 1,
                    event_type=RunEventType.DELEGATE_FINISH,
                    payload=_delegate_finish_payload(
                        task=task,
                        status=DelegationStatus.FAILED,
                        step_count=step_count,
                        error_message=error_message,
                    ),
                )
            )
            return DelegationResult(
                task=task,
                status=DelegationStatus.FAILED,
                child_events=child_events,
                parent_events=parent_events,
                error_message=error_message,
            )

        child_events = tuple(child_result.events)
        parent_events.extend(_delegate_event_events(task, child_events, len(parent_events)))
        step_count = _step_count(child_events)
        budget_error = _observed_step_budget_error(task, budget, step_count)
        if budget_error:
            parent_events.append(
                _parent_event(
                    task=task,
                    index=len(parent_events) + 1,
                    event_type=RunEventType.DELEGATE_FINISH,
                    payload=_delegate_finish_payload(
                        task=task,
                        status=DelegationStatus.FAILED,
                        step_count=step_count,
                        error_message=budget_error,
                    ),
                )
            )
            return DelegationResult(
                task=task,
                status=DelegationStatus.FAILED,
                child_events=child_events,
                parent_events=parent_events,
                error_message=budget_error,
            )

        parent_events.append(
            _parent_event(
                task=task,
                index=len(parent_events) + 1,
                event_type=RunEventType.DELEGATE_FINISH,
                payload=_delegate_finish_payload(
                    task=task,
                    status=DelegationStatus.COMPLETED,
                    step_count=step_count,
                    final_message=child_result.final_message,
                ),
            )
        )
        return DelegationResult(
            task=task,
            status=DelegationStatus.COMPLETED,
            final_message=child_result.final_message,
            child_events=child_events,
            parent_events=parent_events,
        )

    def run_many(
        self,
        tasks: Sequence[DelegationTask],
        budget: DelegationBudget = DEFAULT_DELEGATION_BUDGET,
    ) -> tuple[DelegationResult, ...]:
        task_tuple = tuple(tasks)
        _validate_unique_values(
            "task id",
            tuple(task.id for task in task_tuple),
        )
        _validate_unique_values(
            "child_run_id",
            tuple(task.child_run_id for task in task_tuple),
        )
        if len(task_tuple) > budget.max_child_runs:
            raise ValueError(
                f"child task count {len(task_tuple)} exceeds max_child_runs "
                f"{budget.max_child_runs}"
            )
        for task in task_tuple:
            _validate_task_budget(task, budget)

        results: list[DelegationResult] = []
        remaining_steps = budget.max_total_steps
        for task in task_tuple:
            allowed_max_steps = _allowed_max_steps(task, budget)
            if allowed_max_steps > remaining_steps:
                raise ValueError(
                    f"task {task.id} allowed max steps {allowed_max_steps} exceeds "
                    f"remaining max_total_steps {remaining_steps}"
                )
            result = self.run_task(task, budget=budget)
            if result.step_count > remaining_steps:
                raise ValueError(
                    f"task {task.id} observed step count {result.step_count} exceeds "
                    f"remaining max_total_steps {remaining_steps}"
                )
            remaining_steps -= result.step_count
            results.append(result)
        return tuple(results)


def compile_child_prompt(task: DelegationTask) -> str:
    lines = [
        "Objective:",
        task.objective,
        "",
        "Context Messages:",
    ]
    if not task.context_messages:
        lines.append("- None")
    else:
        lines.extend(
            f"- {message.id} ({message.role.value}): {message.content}"
            for message in task.context_messages
        )
    return "\n".join(lines)


def _validate_task_budget(task: DelegationTask, budget: DelegationBudget) -> None:
    if task.role.max_steps > budget.max_steps_per_child:
        raise ValueError(
            f"task {task.id} role max_steps {task.role.max_steps} exceeds "
            f"max_steps_per_child {budget.max_steps_per_child}"
        )
    if _allowed_max_steps(task, budget) > budget.max_total_steps:
        raise ValueError(
            f"task {task.id} allowed max steps {_allowed_max_steps(task, budget)} exceeds "
            f"max_total_steps {budget.max_total_steps}"
        )


def _allowed_max_steps(task: DelegationTask, budget: DelegationBudget) -> int:
    return min(task.role.max_steps, budget.max_steps_per_child)


def _validate_unique_values(name: str, values: Sequence[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {name}: {value}")
        seen.add(value)


def _parent_event(
    *,
    task: DelegationTask,
    index: int,
    event_type: RunEventType,
    payload: dict[str, object],
) -> RunEvent:
    return RunEvent(
        id=f"{task.id}_delegate_{index}",
        run_id=task.parent_run_id,
        type=event_type,
        payload=payload,
    )


def _delegate_start_payload(
    task: DelegationTask,
    budget: DelegationBudget,
) -> dict[str, object]:
    return {
        "task_id": task.id,
        "parent_run_id": task.parent_run_id,
        "child_run_id": task.child_run_id,
        "role_id": task.role.id,
        "tool_names": task.role.tool_names,
        "skill_names": task.role.skill_names,
        "memory_kinds": task.role.memory_kinds,
        "budget": budget.to_record(),
    }


def _delegate_event_events(
    task: DelegationTask,
    child_events: Sequence[RunEvent],
    offset: int,
) -> tuple[RunEvent, ...]:
    return tuple(
        _parent_event(
            task=task,
            index=offset + index,
            event_type=RunEventType.DELEGATE_EVENT,
            payload={
                "task_id": task.id,
                "child_run_id": task.child_run_id,
                "child_event": child_event.to_record(),
            },
        )
        for index, child_event in enumerate(child_events, start=1)
    )


def _delegate_finish_payload(
    *,
    task: DelegationTask,
    status: DelegationStatus,
    step_count: int,
    final_message: AgentMessage | None = None,
    error_message: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "task_id": task.id,
        "child_run_id": task.child_run_id,
        "status": status.value,
        "step_count": step_count,
    }
    if final_message is not None:
        payload["final_message"] = _message_to_record(final_message)
    if error_message:
        payload["error"] = error_message
    return payload


def _message_to_record(message: AgentMessage) -> dict[str, object]:
    return {
        "id": message.id,
        "role": message.role.value,
        "content": message.content,
        "metadata": thaw_json_value(freeze_json_value(dict(message.metadata))),
    }


def _exception_events(exc: Exception, *, task: DelegationTask) -> tuple[RunEvent, ...]:
    try:
        events = getattr(exc, "events", ())
        if events is None:
            return ()
        event_tuple = tuple(events)
    except Exception:
        return ()
    if any(not isinstance(event, RunEvent) for event in event_tuple):
        return ()
    if any(event.run_id != task.child_run_id for event in event_tuple):
        return ()
    return event_tuple


def _step_count(events: Sequence[RunEvent]) -> int:
    return sum(1 for event in events if event.type == RunEventType.MODEL_REQUEST)


def _observed_step_budget_error(
    task: DelegationTask,
    budget: DelegationBudget,
    step_count: int,
) -> str:
    allowed_max_steps = _allowed_max_steps(task, budget)
    if step_count <= allowed_max_steps:
        return ""
    return (
        f"child step count {step_count} exceeds allowed max steps {allowed_max_steps} "
        f"(role max_steps {task.role.max_steps}, "
        f"max_steps_per_child {budget.max_steps_per_child})"
    )

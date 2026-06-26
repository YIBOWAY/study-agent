from research_core.delegation import (
    AgentRolePolicy,
    DelegationMergeResult,
    DelegationResult,
    DelegationStatus,
    DelegationTask,
)
from research_core.delegation.runtime import compile_child_prompt
from research_core.runtime.messages import AgentMessage, MessageRole


def _role(**overrides: object) -> AgentRolePolicy:
    values = {
        "id": "role_reviewer",
        "name": "Reviewer",
        "system_prompt": "Review only delegated evidence.",
        "max_steps": 4,
    }
    values.update(overrides)
    return AgentRolePolicy(**values)


def _task(**overrides: object) -> DelegationTask:
    values = {
        "id": "task_1",
        "parent_run_id": "parent_run",
        "child_run_id": "child_run_1",
        "objective": "Summarize the supplied filing excerpt.",
        "role": _role(),
    }
    values.update(overrides)
    return DelegationTask(**values)


def test_child_prompt_eval_excludes_private_parent_history_from_task_metadata() -> None:
    prompt = compile_child_prompt(
        _task(
            context_messages=(
                AgentMessage(
                    id="msg_allowed",
                    role=MessageRole.USER,
                    content="Allowed filing excerpt may be used.",
                ),
            ),
            metadata={
                "private_parent_history": "Do not leak this parent-only chain of thought.",
                "parent_history": ["Internal parent summary that must stay private."],
            },
        )
    )

    assert "Allowed filing excerpt may be used." in prompt
    assert "Do not leak this parent-only chain of thought" not in prompt
    assert "Internal parent summary that must stay private" not in prompt


def test_merge_eval_keeps_all_non_completed_children_unresolved() -> None:
    planned = DelegationResult(
        task=_task(id="task_planned", child_run_id="child_run_planned"),
        status=DelegationStatus.PLANNED,
    )
    completed = DelegationResult(
        task=_task(id="task_completed", child_run_id="child_run_completed"),
        status=DelegationStatus.COMPLETED,
    )
    failed = DelegationResult(
        task=_task(id="task_failed", child_run_id="child_run_failed"),
        status=DelegationStatus.FAILED,
        error_message="child failed",
    )
    cancelled = DelegationResult(
        task=_task(id="task_cancelled", child_run_id="child_run_cancelled"),
        status=DelegationStatus.CANCELLED,
    )
    running = DelegationResult(
        task=_task(id="task_running", child_run_id="child_run_running"),
        status=DelegationStatus.RUNNING,
    )

    merge = DelegationMergeResult.from_results(
        [planned, completed, failed, cancelled, running],
        summary="Only completed child results can be accepted without parent review.",
    )

    assert [result.task.id for result in merge.decisions] == [
        "task_planned",
        "task_completed",
        "task_failed",
        "task_cancelled",
        "task_running",
    ]
    assert [result.task.id for result in merge.unresolved_conflicts] == [
        "task_planned",
        "task_failed",
        "task_cancelled",
        "task_running",
    ]

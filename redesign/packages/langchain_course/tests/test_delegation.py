from __future__ import annotations

import pytest
from langchain_course.delegation import (
    DelegationCoordinator,
    DelegationError,
    WorkerBudget,
    WorkerRole,
    WorkerTask,
    compile_child_prompt,
    filter_tools_for_role,
    make_plain_agent_result,
    merge_worker_results,
    scripted_runner,
)
from langchain_course.tools_echo import add, echo


def _role(
    name: str = "researcher",
    *,
    system_prompt: str = "Stay focused on the assigned objective.",
    max_steps: int = 2,
    tool_names: tuple[str, ...] = (),
) -> WorkerRole:
    return WorkerRole(
        name=name,
        system_prompt=system_prompt,
        max_steps=max_steps,
        tool_names=tool_names,
    )


def _task(
    task_id: str = "t1",
    *,
    role: WorkerRole | None = None,
    objective: str = "Summarize the findings.",
    context_messages: tuple[str, ...] = (),
) -> WorkerTask:
    return WorkerTask(
        task_id=task_id,
        role=role or _role(),
        objective=objective,
        context_messages=context_messages,
    )


def test_compile_child_prompt_includes_objective_and_allowed_context_only() -> None:
    task = _task(
        objective="Draft a short outline.",
        context_messages=("Use source A", "Prefer short bullets"),
    )
    prompt = compile_child_prompt(task)

    assert "Objective: Draft a short outline." in prompt
    assert "Allowed context:" in prompt
    assert "1. Use source A" in prompt
    assert "2. Prefer short bullets" in prompt
    assert "Do not invent parent-private history." in prompt
    assert "parent secret" not in prompt
    assert "API_KEY" not in prompt


def test_filter_tools_for_role_empty_returns_all_nonempty_filters() -> None:
    tools = [echo, add]
    all_tools = filter_tools_for_role(_role(tool_names=()), tools)
    assert [t.name for t in all_tools] == ["echo", "add"]

    only_echo = filter_tools_for_role(_role(tool_names=("echo",)), tools)
    assert [t.name for t in only_echo] == ["echo"]

    none = filter_tools_for_role(_role(tool_names=("missing",)), tools)
    assert none == []


def test_run_task_success_records_delegate_start_and_finish() -> None:
    coordinator = DelegationCoordinator()
    task = _task(task_id="ok-1", objective="Find two citations.")
    budget = WorkerBudget(max_workers=2, max_steps_per_worker=3, max_total_steps=6)
    runner = scripted_runner(
        {"ok-1": make_plain_agent_result("citation A and B", model_requests=1)}
    )

    result = coordinator.run_task(task, budget, runner=runner)

    assert result.status == "completed"
    assert result.final_text == "citation A and B"
    assert result.step_count == 1
    assert result.error_message == ""
    assert coordinator.parent_step_kinds() == ["delegate_start", "delegate_finish"]
    start = coordinator.parent_steps[0]
    finish = coordinator.parent_steps[1]
    assert start.payload["task_id"] == "ok-1"
    assert start.payload["role"] == "researcher"
    assert finish.payload["status"] == "completed"


def test_run_task_role_max_steps_exceeds_budget_raises() -> None:
    coordinator = DelegationCoordinator()
    task = _task(role=_role(max_steps=5))
    budget = WorkerBudget(max_workers=1, max_steps_per_worker=2, max_total_steps=10)
    runner = scripted_runner({"t1": make_plain_agent_result("unused")})

    with pytest.raises(DelegationError, match="exceeds"):
        coordinator.run_task(task, budget, runner=runner)


def test_run_task_exhausted_total_steps_raises() -> None:
    coordinator = DelegationCoordinator()
    task = _task()
    budget = WorkerBudget(max_workers=1, max_steps_per_worker=2, max_total_steps=4)
    runner = scripted_runner({"t1": make_plain_agent_result("unused")})

    with pytest.raises(DelegationError, match="no remaining total steps"):
        coordinator.run_task(task, budget, runner=runner, steps_used=4)


def test_run_task_budget_exceeded_marks_failed() -> None:
    coordinator = DelegationCoordinator()
    task = _task(role=_role(max_steps=1))
    budget = WorkerBudget(max_workers=1, max_steps_per_worker=1, max_total_steps=5)
    runner = scripted_runner(
        {"t1": make_plain_agent_result("too many steps", model_requests=3)}
    )

    result = coordinator.run_task(task, budget, runner=runner)

    assert result.status == "failed"
    assert result.step_count == 3
    assert "budget exceeded" in result.error_message
    assert "3 > cap 1" in result.error_message
    assert coordinator.parent_step_kinds() == ["delegate_start", "delegate_finish"]


def test_run_task_runner_exception_marks_failed_with_parent_trail() -> None:
    coordinator = DelegationCoordinator()
    task = _task(task_id="boom")
    budget = WorkerBudget(max_workers=1, max_steps_per_worker=2, max_total_steps=4)

    def bad_runner(_task: WorkerTask, _tools) -> object:
        raise RuntimeError("child crashed")

    result = coordinator.run_task(task, budget, runner=bad_runner)  # type: ignore[arg-type]

    assert result.status == "failed"
    assert result.final_text == ""
    assert result.step_count == 0
    assert "RuntimeError" in result.error_message
    assert "child crashed" in result.error_message
    assert coordinator.parent_step_kinds() == ["delegate_start", "delegate_finish"]
    assert coordinator.parent_steps[1].payload["status"] == "failed"


def test_run_many_exceeds_max_workers_raises() -> None:
    coordinator = DelegationCoordinator()
    tasks = [
        _task(task_id="a"),
        _task(task_id="b"),
        _task(task_id="c"),
    ]
    budget = WorkerBudget(max_workers=2, max_steps_per_worker=2, max_total_steps=10)
    runner = scripted_runner(
        {
            "a": make_plain_agent_result("A"),
            "b": make_plain_agent_result("B"),
            "c": make_plain_agent_result("C"),
        }
    )

    with pytest.raises(DelegationError, match="max_workers"):
        coordinator.run_many(tasks, budget, runner=runner)


def test_run_many_mixed_results_merge_decisions_and_conflicts() -> None:
    coordinator = DelegationCoordinator()
    ok_role = _role(name="writer", max_steps=2)
    fail_role = _role(name="critic", max_steps=1)
    tasks = [
        _task(task_id="ok", role=ok_role, objective="Write claim"),
        _task(task_id="bad", role=fail_role, objective="Review claim"),
    ]
    budget = WorkerBudget(max_workers=3, max_steps_per_worker=2, max_total_steps=10)
    runner = scripted_runner(
        {
            "ok": make_plain_agent_result("Claim is solid.", model_requests=1),
            "bad": make_plain_agent_result("over budget", model_requests=3),
        }
    )

    merged = coordinator.run_many(tasks, budget, runner=runner)

    assert len(merged.worker_results) == 2
    assert merged.decisions == ("ok: Claim is solid.",)
    assert len(merged.unresolved_conflicts) == 1
    assert merged.unresolved_conflicts[0].startswith("bad:")
    assert "budget exceeded" in merged.unresolved_conflicts[0]
    assert "1 completed, 1 unresolved conflict(s)" in merged.summary


def test_merge_summary_strings_sensible() -> None:
    from langchain_course.delegation import WorkerResult

    all_ok = merge_worker_results(
        [
            WorkerResult(
                task_id="a",
                status="completed",
                final_text=" Alpha ",
                steps=(),
                step_count=1,
            ),
            WorkerResult(
                task_id="b",
                status="completed",
                final_text="Beta",
                steps=(),
                step_count=1,
            ),
        ]
    )
    assert all_ok.decisions == ("a: Alpha", "b: Beta")
    assert all_ok.unresolved_conflicts == ()
    assert all_ok.summary == "2 completed, no unresolved conflicts"

    mixed = merge_worker_results(
        [
            WorkerResult(
                task_id="a",
                status="completed",
                final_text="ok",
                steps=(),
                step_count=1,
            ),
            WorkerResult(
                task_id="b",
                status="failed",
                final_text="",
                steps=(),
                step_count=0,
                error_message="timeout",
            ),
            WorkerResult(
                task_id="c",
                status="failed",
                final_text="",
                steps=(),
                step_count=0,
            ),
        ]
    )
    assert mixed.decisions == ("a: ok",)
    assert mixed.unresolved_conflicts == (
        "b: timeout",
        "c: worker failed without message",
    )
    assert mixed.summary == "1 completed, 2 unresolved conflict(s)"


def test_worker_role_task_budget_validation() -> None:
    with pytest.raises(DelegationError, match="role name"):
        WorkerRole(name="  ", system_prompt="ok")
    with pytest.raises(DelegationError, match="system_prompt"):
        WorkerRole(name="r", system_prompt="")
    with pytest.raises(DelegationError, match="max_steps"):
        WorkerRole(name="r", system_prompt="ok", max_steps=0)

    role = _role()
    with pytest.raises(DelegationError, match="task_id"):
        WorkerTask(task_id="", role=role, objective="do work")
    with pytest.raises(DelegationError, match="objective"):
        WorkerTask(task_id="t", role=role, objective="   ")

    with pytest.raises(DelegationError, match="max_workers"):
        WorkerBudget(max_workers=0)
    with pytest.raises(DelegationError, match="max_steps_per_worker"):
        WorkerBudget(max_steps_per_worker=0)
    with pytest.raises(DelegationError, match="max_total_steps"):
        WorkerBudget(max_total_steps=0)


def test_parent_step_kinds_order_for_run_many() -> None:
    coordinator = DelegationCoordinator()
    tasks = [
        _task(task_id="w1", objective="First"),
        _task(task_id="w2", objective="Second"),
    ]
    budget = WorkerBudget(max_workers=3, max_steps_per_worker=2, max_total_steps=10)
    runner = scripted_runner(
        {
            "w1": make_plain_agent_result("one"),
            "w2": make_plain_agent_result("two"),
        }
    )

    coordinator.run_many(tasks, budget, runner=runner)

    assert coordinator.parent_step_kinds() == [
        "delegate_start",
        "delegate_finish",
        "delegate_start",
        "delegate_finish",
    ]
    assert coordinator.parent_steps[0].payload["task_id"] == "w1"
    assert coordinator.parent_steps[2].payload["task_id"] == "w2"

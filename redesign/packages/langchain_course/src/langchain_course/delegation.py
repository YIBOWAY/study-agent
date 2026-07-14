"""Part 4: multi-worker delegation with budgets and isolated child context."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from langchain_core.runnables import Runnable, RunnableParallel
from langchain_core.tools import BaseTool

from langchain_course.agent_kernel import AgentRunResult, AgentStep


class DelegationError(ValueError):
    """Raised for invalid delegation setup (budget/role) before a worker runs."""


@dataclass(frozen=True, slots=True)
class WorkerRole:
    name: str
    system_prompt: str
    max_steps: int = 4
    tool_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DelegationError("role name must be non-empty")
        if not self.system_prompt.strip():
            raise DelegationError("role system_prompt must be non-empty")
        if self.max_steps < 1:
            raise DelegationError("role max_steps must be >= 1")


@dataclass(frozen=True, slots=True)
class WorkerTask:
    task_id: str
    role: WorkerRole
    objective: str
    context_messages: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise DelegationError("task_id must be non-empty")
        if not self.objective.strip():
            raise DelegationError("objective must be non-empty")


@dataclass(frozen=True, slots=True)
class WorkerBudget:
    max_workers: int = 3
    max_steps_per_worker: int = 4
    max_total_steps: int = 12

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise DelegationError("max_workers must be >= 1")
        if self.max_steps_per_worker < 1:
            raise DelegationError("max_steps_per_worker must be >= 1")
        if self.max_total_steps < 1:
            raise DelegationError("max_total_steps must be >= 1")


@dataclass(frozen=True, slots=True)
class WorkerResult:
    task_id: str
    status: str  # completed | failed
    final_text: str
    steps: tuple[AgentStep, ...]
    step_count: int
    error_message: str = ""

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "final_text": self.final_text,
            "step_count": self.step_count,
            "error_message": self.error_message,
            "step_kinds": [s.kind for s in self.steps],
        }


@dataclass(frozen=True, slots=True)
class MergeResult:
    decisions: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    summary: str
    worker_results: tuple[WorkerResult, ...] = ()

    def to_record(self) -> dict[str, Any]:
        return {
            "decisions": list(self.decisions),
            "unresolved_conflicts": list(self.unresolved_conflicts),
            "summary": self.summary,
            "worker_results": [r.to_record() for r in self.worker_results],
        }


WorkerRunner = Callable[[WorkerTask, Sequence[BaseTool]], AgentRunResult]


def build_parallel_worker_runnable(
    workers: Mapping[str, Runnable[Any, Any]],
) -> RunnableParallel[Any]:
    """Compose independent LangChain workers with `RunnableParallel`.

    This teaches genuine LC composition. The budgeted coordinator below remains
    sequential because budget/side-effect accounting is a separate product
    contract that `RunnableParallel` does not provide automatically.
    """
    if not workers:
        raise DelegationError("parallel workers must not be empty")
    if any(not name.strip() for name in workers):
        raise DelegationError("parallel worker names must be non-empty")
    return RunnableParallel(dict(workers))


def compile_child_prompt(task: WorkerTask) -> str:
    """Build the only user message the child should see (isolated context)."""
    parts = [
        f"Role: {task.role.name}",
        f"Role instructions: {task.role.system_prompt}",
        f"Objective: {task.objective}",
    ]
    if task.context_messages:
        parts.append("Allowed context:")
        for i, msg in enumerate(task.context_messages, start=1):
            parts.append(f"{i}. {msg}")
    parts.append(
        "Answer only from the objective and allowed context. "
        "Do not invent parent-private history."
    )
    return "\n".join(parts)


def filter_tools_for_role(
    role: WorkerRole, tools: Sequence[BaseTool]
) -> list[BaseTool]:
    """Honor role.tool_names when non-empty; otherwise return all tools."""
    if not role.tool_names:
        return list(tools)
    allowed = set(role.tool_names)
    return [tool for tool in tools if tool.name in allowed]


def _count_model_requests(result: AgentRunResult) -> int:
    return sum(1 for step in result.steps if step.kind == "model_request")


def merge_worker_results(results: Sequence[WorkerResult]) -> MergeResult:
    decisions: list[str] = []
    conflicts: list[str] = []
    for result in results:
        if result.status == "completed" and result.final_text.strip():
            decisions.append(f"{result.task_id}: {result.final_text.strip()}")
        else:
            msg = result.error_message or "worker failed without message"
            conflicts.append(f"{result.task_id}: {msg}")
    if conflicts:
        summary = (
            f"{len(decisions)} completed, {len(conflicts)} unresolved conflict(s)"
        )
    else:
        summary = f"{len(decisions)} completed, no unresolved conflicts"
    return MergeResult(
        decisions=tuple(decisions),
        unresolved_conflicts=tuple(conflicts),
        summary=summary,
        worker_results=tuple(results),
    )


@dataclass
class DelegationCoordinator:
    """Sequential multi-worker coordinator with parent trail and budgets.

    Does not auto-enforce skill/memory allowlists (honest boundary, same lesson
    as handwritten Part 4).

    Budget honesty (intentional teaching design for scripted/offline runners):
    per-worker step caps are enforced *post-hoc* after ``runner`` returns.
    Side effects from the runner may already have happened before the coordinator
    compares model_request count to the cap and marks the WorkerResult failed.
    ``run_many`` soft-fails remaining tasks when total steps are exhausted
    (failed "not run" results) rather than raising mid-loop; ``max_workers``
    is still enforced up front by raising DelegationError.
    """

    parent_steps: list[AgentStep] = field(default_factory=list)

    def run_task(
        self,
        task: WorkerTask,
        budget: WorkerBudget,
        *,
        runner: WorkerRunner,
        tools: Sequence[BaseTool] = (),
        steps_used: int = 0,
    ) -> WorkerResult:
        if task.role.max_steps > budget.max_steps_per_worker:
            raise DelegationError(
                f"role max_steps {task.role.max_steps} exceeds "
                f"budget.max_steps_per_worker {budget.max_steps_per_worker}"
            )
        remaining = budget.max_total_steps - steps_used
        if remaining < 1:
            raise DelegationError("no remaining total steps in budget")

        self.parent_steps.append(
            AgentStep(
                kind="delegate_start",
                payload={
                    "task_id": task.task_id,
                    "role": task.role.name,
                    "objective": task.objective,
                    "context_count": len(task.context_messages),
                },
            )
        )

        child_tools = filter_tools_for_role(task.role, tools)
        try:
            agent_result = runner(task, child_tools)
        except Exception as exc:  # noqa: BLE001 - surface as failed worker result
            result = WorkerResult(
                task_id=task.task_id,
                status="failed",
                final_text="",
                steps=(),
                step_count=0,
                error_message=f"{type(exc).__name__}: {exc}",
            )
            self.parent_steps.append(
                AgentStep(
                    kind="delegate_finish",
                    payload=result.to_record(),
                )
            )
            return result

        step_count = _count_model_requests(agent_result)
        # Post-hoc: runner already returned; side effects may have occurred.
        per_cap = min(task.role.max_steps, budget.max_steps_per_worker, remaining)
        if step_count > per_cap:
            result = WorkerResult(
                task_id=task.task_id,
                status="failed",
                final_text=agent_result.final_text,
                steps=tuple(agent_result.steps),
                step_count=step_count,
                error_message=(
                    f"budget exceeded: model_request steps {step_count} > cap {per_cap}"
                ),
            )
        else:
            result = WorkerResult(
                task_id=task.task_id,
                status="completed",
                final_text=agent_result.final_text,
                steps=tuple(agent_result.steps),
                step_count=step_count,
            )

        self.parent_steps.append(
            AgentStep(
                kind="delegate_finish",
                payload=result.to_record(),
            )
        )
        return result

    def run_many(
        self,
        tasks: Sequence[WorkerTask],
        budget: WorkerBudget,
        *,
        runner: WorkerRunner,
        tools: Sequence[BaseTool] = (),
    ) -> MergeResult:
        if len(tasks) > budget.max_workers:
            raise DelegationError(
                f"task count {len(tasks)} exceeds max_workers {budget.max_workers}"
            )
        results: list[WorkerResult] = []
        used = 0
        for index, task in enumerate(tasks):
            remaining = budget.max_total_steps - used
            if remaining < 1:
                # Soft-fail this task and all subsequent ones; do not raise.
                # Still record parent trail so merge results and audit trail agree.
                for leftover in tasks[index:]:
                    skipped = WorkerResult(
                        task_id=leftover.task_id,
                        status="failed",
                        final_text="",
                        steps=(),
                        step_count=0,
                        error_message="not run: no remaining total steps",
                    )
                    self.parent_steps.append(
                        AgentStep(
                            kind="delegate_start",
                            payload={
                                "task_id": leftover.task_id,
                                "role": leftover.role.name,
                                "objective": leftover.objective,
                                "context_count": len(leftover.context_messages),
                                "skipped": True,
                                "reason": "no remaining total steps",
                            },
                        )
                    )
                    self.parent_steps.append(
                        AgentStep(
                            kind="delegate_finish",
                            payload=skipped.to_record(),
                        )
                    )
                    results.append(skipped)
                break
            result = self.run_task(
                task,
                budget,
                runner=runner,
                tools=tools,
                steps_used=used,
            )
            results.append(result)
            used += result.step_count
        return merge_worker_results(results)

    def parent_step_kinds(self) -> list[str]:
        return [step.kind for step in self.parent_steps]


def scripted_runner(results_by_task: dict[str, AgentRunResult]) -> WorkerRunner:
    """Build a deterministic runner for offline unit tests."""

    def _run(task: WorkerTask, _tools: Sequence[BaseTool]) -> AgentRunResult:
        if task.task_id not in results_by_task:
            raise KeyError(f"no scripted result for task {task.task_id}")
        return results_by_task[task.task_id]

    return _run


def make_plain_agent_result(text: str, *, model_requests: int = 1) -> AgentRunResult:
    steps: list[AgentStep] = [AgentStep(kind="user_message", payload={})]
    for _ in range(model_requests):
        steps.append(AgentStep(kind="model_request", payload={}))
        steps.append(AgentStep(kind="model_response", payload={"content": text}))
    return AgentRunResult(final_text=text, steps=steps)

"""Part 6: offline build-vs-adopt comparison harness (LangChain track).

Framework profiles are deterministic teaching records — not live wrappers for
third-party SDKs. The LC baseline runs the real Part 1 LangChain tool loop with
a deterministic `BaseChatModel`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from langchain_course.agent_kernel import run_tool_calling_agent, step_kinds
from langchain_course.fake_models import tool_then_final_model
from langchain_course.tools_echo import echo


class ComparisonError(ValueError):
    """Raised when comparison inputs are invalid."""


SCORE_CRITERIA = (
    "inspectability",
    "offline_testing",
    "typed_contracts",
    "state_resume",
    "multi_agent",
    "product_boundary",
    "team_cost",
)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ComparisonError(f"{name} must not be empty")


def _require_score(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
        raise ComparisonError(f"{name} must be a finite number")
    if value < 0.0 or value > 1.0:
        raise ComparisonError(f"{name} must be between 0 and 1 inclusive")
    return float(value)


@dataclass(frozen=True, slots=True)
class ComparisonTask:
    id: str
    title: str
    weights: Mapping[str, float]
    notes: str = ""
    required_capabilities: Sequence[str] = ()

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        weights = dict(self.weights)
        if not weights:
            raise ComparisonError("weights must not be empty")
        for key, value in weights.items():
            if key not in SCORE_CRITERIA:
                raise ComparisonError(f"unknown weight criterion {key!r}")
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(value)
                or value <= 0
            ):
                raise ComparisonError(f"weight for {key!r} must be a positive finite number")
        object.__setattr__(self, "weights", {k: float(v) for k, v in weights.items()})
        object.__setattr__(
            self,
            "required_capabilities",
            tuple(self.required_capabilities),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "weights": dict(self.weights),
            "notes": self.notes,
            "required_capabilities": list(self.required_capabilities),
        }


@dataclass(frozen=True, slots=True)
class TaskRunSummary:
    task_id: str
    final_answer: str
    step_sequence: Sequence[str]
    tool_call_count: int
    error_count: int

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "final_answer": self.final_answer,
            "step_sequence": list(self.step_sequence),
            "tool_call_count": self.tool_call_count,
            "error_count": self.error_count,
        }


@dataclass(frozen=True, slots=True)
class FrameworkProfile:
    id: str
    name: str
    inspectability: float
    offline_testing: float
    typed_contracts: float
    state_resume: float
    multi_agent: float
    product_boundary: float
    team_cost: float
    notes: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("name", self.name)
        for criterion in SCORE_CRITERIA:
            object.__setattr__(
                self,
                criterion,
                _require_score(criterion, getattr(self, criterion)),
            )
        object.__setattr__(self, "notes", tuple(self.notes))

    def score_for(self, criterion: str) -> float:
        if criterion not in SCORE_CRITERIA:
            raise ComparisonError(f"unknown score criterion {criterion!r}")
        return float(getattr(self, criterion))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            **{c: self.score_for(c) for c in SCORE_CRITERIA},
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class FrameworkRecommendation:
    task_id: str
    profile_id: str
    total_score: float
    strengths: Sequence[str]
    tradeoffs: Sequence[str]

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "profile_id": self.profile_id,
            "total_score": self.total_score,
            "strengths": list(self.strengths),
            "tradeoffs": list(self.tradeoffs),
        }


def score_profile_for_task(
    profile: FrameworkProfile,
    task: ComparisonTask,
) -> FrameworkRecommendation:
    weighted_sum = 0.0
    weight_total = 0.0
    strengths: list[str] = []
    tradeoffs: list[str] = []
    for criterion, weight in task.weights.items():
        score = profile.score_for(criterion)
        weighted_sum += score * weight
        weight_total += weight
        if score >= 0.80:
            strengths.append(criterion)
        elif score < 0.55:
            tradeoffs.append(criterion)
    total = round(weighted_sum / weight_total, 4)
    return FrameworkRecommendation(
        task_id=task.id,
        profile_id=profile.id,
        total_score=total,
        strengths=tuple(strengths),
        tradeoffs=tuple(tradeoffs),
    )


def build_recommendation_matrix(
    task: ComparisonTask,
    profiles: Sequence[FrameworkProfile],
) -> tuple[FrameworkRecommendation, ...]:
    if not profiles:
        raise ComparisonError("profiles must not be empty")
    return tuple(score_profile_for_task(profile, task) for profile in profiles)


def recommend_profile(
    matrix: Sequence[FrameworkRecommendation],
    *,
    task_id: str,
) -> FrameworkRecommendation:
    candidates = [row for row in matrix if row.task_id == task_id]
    if not candidates:
        raise ComparisonError(f"no recommendations for task_id {task_id!r}")
    # tie-break: higher total first, then stable profile_id ascending
    ordered = sorted(candidates, key=lambda row: (-row.total_score, row.profile_id))
    return ordered[0]


def default_framework_profiles() -> tuple[FrameworkProfile, ...]:
    """Deterministic scorecards for teaching after learners used real LC."""
    return (
        FrameworkProfile(
            id="handwritten",
            name="Handwritten research_core",
            inspectability=0.95,
            offline_testing=0.95,
            typed_contracts=0.9,
            state_resume=0.45,
            multi_agent=0.7,
            product_boundary=0.9,
            team_cost=0.55,
            notes=(
                "Strong offline contracts and event trail.",
                "State resume is intentionally thin without a graph runtime.",
            ),
        ),
        FrameworkProfile(
            id="langchain",
            name="LangChain (this track)",
            inspectability=0.75,
            offline_testing=0.7,
            typed_contracts=0.65,
            state_resume=0.55,
            multi_agent=0.75,
            product_boundary=0.7,
            team_cost=0.8,
            notes=(
                "Faster to assemble tool loops and chains.",
                "Inspectability depends on what you record (AgentStep discipline).",
            ),
        ),
        FrameworkProfile(
            id="langgraph",
            name="LangGraph (next track)",
            inspectability=0.8,
            offline_testing=0.65,
            typed_contracts=0.7,
            state_resume=0.95,
            multi_agent=0.85,
            product_boundary=0.7,
            team_cost=0.6,
            notes=(
                "Checkpoint/resume is the headline strength.",
                "Learners should finish LC before LG (F4–F5).",
            ),
        ),
        FrameworkProfile(
            id="crewai",
            name="CrewAI (record only)",
            inspectability=0.5,
            offline_testing=0.4,
            typed_contracts=0.45,
            state_resume=0.4,
            multi_agent=0.9,
            product_boundary=0.45,
            team_cost=0.75,
            notes=("Strong multi-agent demos; weaker offline typed product boundary.",),
        ),
    )


def build_inspectability_task() -> ComparisonTask:
    return ComparisonTask(
        id="task_inspectability",
        title="Prefer inspectable offline research runs",
        weights={
            "inspectability": 3.0,
            "offline_testing": 2.0,
            "typed_contracts": 2.0,
            "product_boundary": 1.0,
            "team_cost": 1.0,
        },
        required_capabilities=("tool_trail", "offline_tests"),
        notes="Weights favor auditability over team onboarding speed.",
    )


def build_state_resume_task() -> ComparisonTask:
    return ComparisonTask(
        id="task_state_resume",
        title="Prefer resumable multi-step workflows",
        weights={
            "state_resume": 4.0,
            "multi_agent": 2.0,
            "inspectability": 1.0,
            "team_cost": 1.0,
        },
        required_capabilities=("checkpoint", "resume"),
        notes="Weights favor graph checkpoint/resume strengths.",
    )


def run_lc_baseline(task: ComparisonTask) -> TaskRunSummary:
    """Offline LC baseline through `bind_tools` + message/tool execution."""
    model = tool_then_final_model(
        tool_name="echo",
        tool_args={"text": task.id},
        final_text=f"LC baseline complete for {task.id}",
    )
    result = run_tool_calling_agent(
        user_message=f"Echo the fixed task id {task.id}, then report completion.",
        tools=[echo],
        model=model,
    )
    kinds = step_kinds(result)
    return TaskRunSummary(
        task_id=task.id,
        final_answer=result.final_text,
        step_sequence=tuple(kinds),
        tool_call_count=sum(1 for kind in kinds if kind == "tool_call"),
        error_count=sum(1 for kind in kinds if kind == "error"),
    )

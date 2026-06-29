from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from research_core.runtime import (
    AgentRunner,
    ToolDefinition,
    ToolRuntime,
    event_type_sequence,
)
from research_core.runtime.immutability import freeze_json_value, thaw_json_value
from research_core.testing import FakeModel, FakeModelResponse

SCORE_CRITERIA = (
    "inspectability",
    "offline_testing",
    "typed_contracts",
    "state_resume",
    "multi_agent",
    "product_boundary",
    "team_cost",
)


@dataclass(frozen=True, slots=True)
class ComparisonTask:
    id: str
    title: str
    system_prompt: str
    user_message: str
    model_responses: Sequence[str]
    tool_name: str
    tool_description: str
    tool_argument_name: str
    required_capabilities: Sequence[str]
    expected_event_sequence: Sequence[str]
    weights: Mapping[str, float]
    notes: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_non_empty("title", self.title)
        _require_non_empty("system_prompt", self.system_prompt)
        _require_non_empty("user_message", self.user_message)
        _require_non_empty("tool_name", self.tool_name)
        _require_non_empty("tool_description", self.tool_description)
        _require_non_empty("tool_argument_name", self.tool_argument_name)
        object.__setattr__(
            self,
            "model_responses",
            _tuple_of_non_empty_strings("model_responses", self.model_responses),
        )
        object.__setattr__(
            self,
            "required_capabilities",
            _tuple_of_non_empty_strings("required_capabilities", self.required_capabilities),
        )
        object.__setattr__(
            self,
            "expected_event_sequence",
            _tuple_of_non_empty_strings("expected_event_sequence", self.expected_event_sequence),
        )
        object.__setattr__(self, "weights", _freeze_weights(self.weights))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "system_prompt": self.system_prompt,
            "user_message": self.user_message,
            "model_responses": list(self.model_responses),
            "tool_name": self.tool_name,
            "tool_description": self.tool_description,
            "tool_argument_name": self.tool_argument_name,
            "required_capabilities": list(self.required_capabilities),
            "expected_event_sequence": list(self.expected_event_sequence),
            "weights": thaw_json_value(self.weights),
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class TaskRunSummary:
    task_id: str
    final_answer: str
    event_sequence: Sequence[str]
    tool_call_count: int
    error_count: int

    def __post_init__(self) -> None:
        _require_non_empty("task_id", self.task_id)
        _require_non_empty("final_answer", self.final_answer)
        object.__setattr__(
            self,
            "event_sequence",
            _tuple_of_non_empty_strings("event_sequence", self.event_sequence),
        )
        if not isinstance(self.tool_call_count, int) or isinstance(self.tool_call_count, bool):
            raise ValueError("tool_call_count must be an integer")
        if not isinstance(self.error_count, int) or isinstance(self.error_count, bool):
            raise ValueError("error_count must be an integer")
        if self.tool_call_count < 0:
            raise ValueError("tool_call_count must not be negative")
        if self.error_count < 0:
            raise ValueError("error_count must not be negative")

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "final_answer": self.final_answer,
            "event_sequence": list(self.event_sequence),
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
            object.__setattr__(self, criterion, _require_score(criterion, getattr(self, criterion)))
        object.__setattr__(self, "notes", _tuple_of_strings("notes", self.notes))

    def score_for(self, criterion: str) -> float:
        if criterion not in SCORE_CRITERIA:
            raise ValueError(f"unknown score criterion {criterion!r}")
        return getattr(self, criterion)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "inspectability": self.inspectability,
            "offline_testing": self.offline_testing,
            "typed_contracts": self.typed_contracts,
            "state_resume": self.state_resume,
            "multi_agent": self.multi_agent,
            "product_boundary": self.product_boundary,
            "team_cost": self.team_cost,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class FrameworkRecommendation:
    task_id: str
    profile_id: str
    profile_name: str
    total_score: float
    strengths: Sequence[str] = ()
    tradeoffs: Sequence[str] = ()

    def __post_init__(self) -> None:
        _require_non_empty("task_id", self.task_id)
        _require_non_empty("profile_id", self.profile_id)
        _require_non_empty("profile_name", self.profile_name)
        object.__setattr__(self, "total_score", _require_score("total_score", self.total_score))
        object.__setattr__(
            self,
            "strengths",
            _tuple_of_strings("strengths", self.strengths),
        )
        object.__setattr__(
            self,
            "tradeoffs",
            _tuple_of_strings("tradeoffs", self.tradeoffs),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "total_score": self.total_score,
            "strengths": list(self.strengths),
            "tradeoffs": list(self.tradeoffs),
        }


def build_echo_tool_task() -> ComparisonTask:
    return ComparisonTask(
        id="echo_tool_trace",
        title="Echo tool trajectory",
        system_prompt="You are careful and expose the event trail.",
        user_message="Echo hello through the tool, then explain the observation.",
        model_responses=(
            '{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"text": "hello"}}}',
            "The echo tool returned hello.",
        ),
        tool_name="echo",
        tool_description="Echo text for a deterministic comparison fixture.",
        tool_argument_name="text",
        required_capabilities=(
            "tool_calling",
            "trajectory_inspection",
            "offline_testing",
        ),
        expected_event_sequence=(
            "model_request",
            "model_response",
            "tool_call",
            "tool_result",
            "model_request",
            "model_response",
        ),
        weights={
            "inspectability": 0.30,
            "offline_testing": 0.25,
            "typed_contracts": 0.15,
            "product_boundary": 0.15,
            "team_cost": 0.10,
            "state_resume": 0.03,
            "multi_agent": 0.02,
        },
        notes="A small task that rewards clear event trails and deterministic local tests.",
    )


def build_state_resume_task() -> ComparisonTask:
    return ComparisonTask(
        id="state_resume_workflow",
        title="State and resume workflow",
        system_prompt="You are careful and preserve resumable state.",
        user_message="Plan a paused research workflow and resume it after human review.",
        model_responses=(
            '{"tool_call": {"id": "call_1", "name": "checkpoint", "arguments": {"text": "pause"}}}',
            "The workflow can resume from the checkpoint after review.",
        ),
        tool_name="checkpoint",
        tool_description="Record a deterministic checkpoint marker.",
        tool_argument_name="text",
        required_capabilities=(
            "checkpointing",
            "resume",
            "human_in_the_loop",
        ),
        expected_event_sequence=(
            "model_request",
            "model_response",
            "tool_call",
            "tool_result",
            "model_request",
            "model_response",
        ),
        weights={
            "state_resume": 0.45,
            "multi_agent": 0.15,
            "typed_contracts": 0.10,
            "inspectability": 0.10,
            "team_cost": 0.10,
            "offline_testing": 0.05,
            "product_boundary": 0.05,
        },
        notes="A heavier task that rewards checkpoint, resume, and human-review ergonomics.",
    )


def run_handwritten_task(task: ComparisonTask) -> TaskRunSummary:
    model = FakeModel(FakeModelResponse(content=response) for response in task.model_responses)
    tools = ToolRuntime()

    def handle_tool(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            value = arguments[task.tool_argument_name]
        except KeyError as exc:
            raise ValueError(
                f"tool arguments must include {task.tool_argument_name!r}"
            ) from exc
        return {task.tool_argument_name: value}

    tools.register(
        ToolDefinition(
            name=task.tool_name,
            description=task.tool_description,
            handler=handle_tool,
        )
    )

    result = AgentRunner(model=model, tools=tools, max_steps=len(task.model_responses)).run(
        run_id=f"run_{task.id}",
        system_prompt=task.system_prompt,
        user_message=task.user_message,
    )
    sequence = tuple(event_type_sequence(result.events))
    return TaskRunSummary(
        task_id=task.id,
        final_answer=result.final_message.content,
        event_sequence=sequence,
        tool_call_count=sequence.count("tool_call"),
        error_count=sequence.count("error"),
    )


def default_framework_profiles() -> tuple[FrameworkProfile, ...]:
    return (
        FrameworkProfile(
            id="handwritten",
            name="Handwritten AgentRunner",
            inspectability=0.95,
            offline_testing=0.95,
            typed_contracts=0.65,
            state_resume=0.25,
            multi_agent=0.45,
            product_boundary=0.95,
            team_cost=0.75,
            notes=(
                "Best baseline for teaching mechanism and trajectory debugging.",
                "Needs more code for advanced state, resume, and distributed orchestration.",
            ),
        ),
        FrameworkProfile(
            id="pydantic-ai",
            name="PydanticAI",
            inspectability=0.75,
            offline_testing=0.75,
            typed_contracts=0.95,
            state_resume=0.45,
            multi_agent=0.45,
            product_boundary=0.65,
            team_cost=0.70,
            notes=(
                "Strong typed contracts and Python ergonomics.",
                "Less compelling when the lesson is raw event-loop mechanics.",
            ),
        ),
        FrameworkProfile(
            id="llamaindex-workflows",
            name="LlamaIndex Workflows",
            inspectability=0.65,
            offline_testing=0.65,
            typed_contracts=0.60,
            state_resume=0.60,
            multi_agent=0.50,
            product_boundary=0.55,
            team_cost=0.55,
            notes=(
                "Useful for retrieval-heavy workflow comparisons.",
                "Can pull the course toward framework-specific abstractions quickly.",
            ),
        ),
        FrameworkProfile(
            id="langgraph",
            name="LangGraph",
            inspectability=0.70,
            offline_testing=0.65,
            typed_contracts=0.55,
            state_resume=0.95,
            multi_agent=0.80,
            product_boundary=0.60,
            team_cost=0.45,
            notes=(
                "Strong fit for checkpoint, resume, and human-in-the-loop graphs.",
                "Higher team-learning cost than the handwritten baseline.",
            ),
        ),
        FrameworkProfile(
            id="openai-agents-sdk",
            name="OpenAI Agents SDK",
            inspectability=0.65,
            offline_testing=0.45,
            typed_contracts=0.80,
            state_resume=0.65,
            multi_agent=0.75,
            product_boundary=0.55,
            team_cost=0.65,
            notes=(
                "Good provider-aligned agent abstraction and handoff story.",
                "Less offline-first than the current course baseline.",
            ),
        ),
        FrameworkProfile(
            id="crewai",
            name="CrewAI",
            inspectability=0.50,
            offline_testing=0.45,
            typed_contracts=0.45,
            state_resume=0.50,
            multi_agent=0.85,
            product_boundary=0.45,
            team_cost=0.50,
            notes=(
                "Natural vocabulary for role-based demos.",
                "Needs careful eval boundaries to avoid role-prompt theater.",
            ),
        ),
    )


def build_recommendation_matrix(
    *,
    tasks: Sequence[ComparisonTask],
    profiles: Sequence[FrameworkProfile],
) -> tuple[FrameworkRecommendation, ...]:
    if not tasks:
        raise ValueError("tasks must not be empty")
    if not profiles:
        raise ValueError("profiles must not be empty")

    recommendations: list[FrameworkRecommendation] = []
    for task in tasks:
        if not isinstance(task, ComparisonTask):
            raise ValueError("tasks must contain ComparisonTask objects")
        for profile in profiles:
            if not isinstance(profile, FrameworkProfile):
                raise ValueError("profiles must contain FrameworkProfile objects")
            recommendations.append(_score_profile_for_task(task, profile))
    return tuple(recommendations)


def recommend_profile(
    matrix: Sequence[FrameworkRecommendation],
    *,
    task_id: str,
) -> FrameworkRecommendation:
    _require_non_empty("task_id", task_id)
    matches = [item for item in matrix if item.task_id == task_id]
    if not matches:
        raise ValueError(f"no recommendations found for task {task_id!r}")
    return sorted(matches, key=lambda item: (-item.total_score, item.profile_id))[0]


def _score_profile_for_task(
    task: ComparisonTask,
    profile: FrameworkProfile,
) -> FrameworkRecommendation:
    weights = thaw_json_value(task.weights)
    weight_total = sum(weights.values())
    score = sum(profile.score_for(criterion) * weight for criterion, weight in weights.items())
    total_score = round(score / weight_total, 4)
    strengths = tuple(
        criterion
        for criterion in SCORE_CRITERIA
        if criterion in weights and profile.score_for(criterion) >= 0.8
    )
    tradeoffs = tuple(
        criterion
        for criterion in SCORE_CRITERIA
        if criterion in weights and profile.score_for(criterion) < 0.55
    )
    return FrameworkRecommendation(
        task_id=task.id,
        profile_id=profile.id,
        profile_name=profile.name,
        total_score=total_score,
        strengths=strengths,
        tradeoffs=tradeoffs,
    )


def _freeze_weights(weights: Mapping[str, float]) -> Mapping[str, Any]:
    unknown = sorted(set(weights) - set(SCORE_CRITERIA))
    if unknown:
        raise ValueError(f"unknown weight criteria: {', '.join(unknown)}")
    if not weights:
        raise ValueError("weights must not be empty")
    frozen: dict[str, float] = {}
    for criterion, value in weights.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
            raise ValueError(f"{criterion} weight must be a finite number")
        if value <= 0:
            raise ValueError(f"{criterion} weight must be positive")
        frozen[criterion] = float(value)
    return freeze_json_value(frozen)


def _tuple_of_non_empty_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result = _tuple_of_strings(name, values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _tuple_of_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ValueError(f"{name} must be a sequence of strings")
    result = tuple(values)
    for value in result:
        _require_non_empty(name, value)
    return result


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_score(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"{name} must be a number between 0 and 1")
    score = float(value)
    if score < 0 or score > 1:
        raise ValueError(f"{name} must be a number between 0 and 1")
    return score

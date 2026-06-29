import json
from dataclasses import replace

import pytest

from course.framework_comparisons import (
    ComparisonTask,
    FrameworkProfile,
    FrameworkRecommendation,
    TaskRunSummary,
    build_echo_tool_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
    run_handwritten_task,
)


def test_required_public_framework_comparison_names_are_exported() -> None:
    assert ComparisonTask.__name__ == "ComparisonTask"
    assert TaskRunSummary.__name__ == "TaskRunSummary"
    assert FrameworkProfile.__name__ == "FrameworkProfile"
    assert FrameworkRecommendation.__name__ == "FrameworkRecommendation"
    assert build_echo_tool_task.__name__ == "build_echo_tool_task"
    assert build_state_resume_task.__name__ == "build_state_resume_task"
    assert run_handwritten_task.__name__ == "run_handwritten_task"
    assert default_framework_profiles.__name__ == "default_framework_profiles"
    assert build_recommendation_matrix.__name__ == "build_recommendation_matrix"
    assert recommend_profile.__name__ == "recommend_profile"


def test_echo_tool_task_uses_shared_fixture_and_expected_event_sequence() -> None:
    task = build_echo_tool_task()

    assert task.id == "echo_tool_trace"
    assert task.tool_name == "echo"
    assert task.required_capabilities == (
        "tool_calling",
        "trajectory_inspection",
        "offline_testing",
    )
    assert task.expected_event_sequence == (
        "model_request",
        "model_response",
        "tool_call",
        "tool_result",
        "model_request",
        "model_response",
    )
    assert json.loads(json.dumps(task.to_record(), allow_nan=False)) == task.to_record()


def test_handwritten_runner_executes_echo_task_with_real_trajectory() -> None:
    task = build_echo_tool_task()

    summary = run_handwritten_task(task)

    assert summary.task_id == task.id
    assert summary.final_answer == "The echo tool returned hello."
    assert summary.event_sequence == task.expected_event_sequence
    assert summary.tool_call_count == 1
    assert summary.error_count == 0
    assert summary.to_record() == {
        "task_id": "echo_tool_trace",
        "final_answer": "The echo tool returned hello.",
        "event_sequence": [
            "model_request",
            "model_response",
            "tool_call",
            "tool_result",
            "model_request",
            "model_response",
        ],
        "tool_call_count": 1,
        "error_count": 0,
    }


def test_framework_profile_and_task_contracts_reject_invalid_values() -> None:
    invalid_cases = [
        (
            lambda: FrameworkProfile(
                id=" ",
                name="Handwritten",
                inspectability=1.0,
                offline_testing=1.0,
                typed_contracts=1.0,
                state_resume=1.0,
                multi_agent=1.0,
                product_boundary=1.0,
                team_cost=1.0,
            ),
            "id must not be empty",
        ),
        (
            lambda: FrameworkProfile(
                id="bad",
                name="Bad",
                inspectability=1.1,
                offline_testing=1.0,
                typed_contracts=1.0,
                state_resume=1.0,
                multi_agent=1.0,
                product_boundary=1.0,
                team_cost=1.0,
            ),
            "inspectability must be a number between 0 and 1",
        ),
        (
            lambda: replace(build_echo_tool_task(), model_responses=()),
            "model_responses must not be empty",
        ),
        (
            lambda: ComparisonTask(
                id="bad_task",
                title="Bad task",
                system_prompt="You are careful.",
                user_message="Run this.",
                model_responses=("Final.",),
                tool_name="echo",
                tool_description="Echo text.",
                tool_argument_name="text",
                required_capabilities=("tool_calling",),
                expected_event_sequence=("model_request", "model_response"),
                weights={"unknown": 1.0},
            ),
            "unknown weight criteria",
        ),
    ]

    for build_invalid, expected_message in invalid_cases:
        try:
            build_invalid()
        except ValueError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError(f"Expected invalid comparison contract: {expected_message}")


def test_handwritten_runner_reports_missing_tool_argument_with_error_event() -> None:
    task = replace(
        build_echo_tool_task(),
        model_responses=(
            '{"tool_call": {"id": "call_1", "name": "echo", "arguments": {"wrong": "hello"}}}',
        ),
    )

    with pytest.raises(ValueError, match="tool arguments must include 'text'") as exc_info:
        run_handwritten_task(task)

    events = exc_info.value.events  # type: ignore[attr-defined]
    assert [event.type.value for event in events][-1] == "error"
    assert events[-1].payload["error"] == {
        "kind": "tool_error",
        "message": "tool arguments must include 'text'",
    }


def test_recommendation_matrix_is_json_compatible_and_prefers_handwritten_for_echo() -> None:
    task = build_echo_tool_task()
    profiles = default_framework_profiles()

    matrix = build_recommendation_matrix(tasks=[task], profiles=profiles)
    recommendation = recommend_profile(matrix, task_id=task.id)

    assert recommendation.profile_id == "handwritten"
    assert recommendation.task_id == "echo_tool_trace"
    assert recommendation.total_score > 0.8
    assert "inspectability" in recommendation.strengths
    assert json.loads(json.dumps([item.to_record() for item in matrix], allow_nan=False)) == [
        item.to_record() for item in matrix
    ]


def test_state_resume_weight_prefers_langgraph_profile() -> None:
    task = build_state_resume_task()

    matrix = build_recommendation_matrix(tasks=[task], profiles=default_framework_profiles())
    recommendation = recommend_profile(matrix, task_id=task.id)

    assert recommendation.profile_id == "langgraph"
    assert recommendation.task_id == "state_resume_workflow"
    assert "state_resume" in recommendation.strengths
    assert "team_cost" in recommendation.tradeoffs

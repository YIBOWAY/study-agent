from __future__ import annotations

import pytest
from langchain_course.comparisons import (
    SCORE_CRITERIA,
    ComparisonError,
    ComparisonTask,
    FrameworkProfile,
    build_inspectability_task,
    build_recommendation_matrix,
    build_state_resume_task,
    default_framework_profiles,
    recommend_profile,
    run_lc_baseline,
    score_profile_for_task,
)


def test_score_criteria_stable() -> None:
    assert "inspectability" in SCORE_CRITERIA
    assert "state_resume" in SCORE_CRITERIA
    assert len(SCORE_CRITERIA) == 7


def test_inspectability_task_prefers_handwritten() -> None:
    task = build_inspectability_task()
    profiles = default_framework_profiles()
    matrix = build_recommendation_matrix(task, profiles)
    winner = recommend_profile(matrix, task_id=task.id)
    assert winner.profile_id == "handwritten"
    assert winner.total_score > 0.8
    assert "inspectability" in winner.strengths


def test_state_resume_task_prefers_langgraph() -> None:
    task = build_state_resume_task()
    matrix = build_recommendation_matrix(task, default_framework_profiles())
    winner = recommend_profile(matrix, task_id=task.id)
    assert winner.profile_id == "langgraph"


def test_total_score_is_recomputable() -> None:
    task = ComparisonTask(
        id="t1",
        title="tiny",
        weights={"inspectability": 1.0, "team_cost": 1.0},
    )
    profile = FrameworkProfile(
        id="p",
        name="P",
        inspectability=1.0,
        offline_testing=0.5,
        typed_contracts=0.5,
        state_resume=0.5,
        multi_agent=0.5,
        product_boundary=0.5,
        team_cost=0.0,
    )
    rec = score_profile_for_task(profile, task)
    assert rec.total_score == 0.5
    assert "inspectability" in rec.strengths
    assert "team_cost" in rec.tradeoffs


def test_tie_break_by_profile_id() -> None:
    task = ComparisonTask(id="t", title="t", weights={"inspectability": 1.0})
    a = FrameworkProfile(
        id="b_profile",
        name="B",
        inspectability=0.9,
        offline_testing=0.5,
        typed_contracts=0.5,
        state_resume=0.5,
        multi_agent=0.5,
        product_boundary=0.5,
        team_cost=0.5,
    )
    b = FrameworkProfile(
        id="a_profile",
        name="A",
        inspectability=0.9,
        offline_testing=0.5,
        typed_contracts=0.5,
        state_resume=0.5,
        multi_agent=0.5,
        product_boundary=0.5,
        team_cost=0.5,
    )
    matrix = build_recommendation_matrix(task, (a, b))
    winner = recommend_profile(matrix, task_id="t")
    assert winner.profile_id == "a_profile"


def test_run_lc_baseline_structure() -> None:
    task = build_inspectability_task()
    summary = run_lc_baseline(task)
    assert summary.task_id == task.id
    assert summary.tool_call_count == 1
    assert summary.error_count == 0
    assert "model_request" in summary.step_sequence
    assert "user_message" in summary.step_sequence
    assert "model_response" in summary.step_sequence
    assert "tool_call" in summary.step_sequence
    rec = summary.to_record()
    assert rec["final_answer"]


def test_unknown_weight_rejected() -> None:
    with pytest.raises(ComparisonError, match="unknown weight"):
        ComparisonTask(id="t", title="t", weights={"not_a_criterion": 1.0})

from __future__ import annotations

import pytest

from app.services.agent_evaluator import evaluate_agent_batch, evaluate_agent_run


@pytest.mark.asyncio
async def test_evaluate_agent_run_keyword_coverage() -> None:
    async def run_fn(**kwargs: object) -> dict[str, object]:
        return {
            "report": "Phase 7 adds evaluation and guardrails.",
            "iterations_used": 2,
            "search_result_count": 3,
        }

    result = await evaluate_agent_run(
        {
            "topic": "Phase 7",
            "expected_keywords": ["evaluation", "guardrails", "tracing"],
            "max_iterations": 3,
            "mode": "agent_v2",
        },
        run_fn,
    )

    assert result["completed"] is True
    assert result["keyword_coverage"] == pytest.approx(2 / 3)
    assert result["iterations_used"] == 2
    assert result["search_count"] == 3
    assert result["error"] == ""


@pytest.mark.asyncio
async def test_evaluate_agent_run_failure() -> None:
    async def run_fn(**kwargs: object) -> dict[str, object]:
        raise RuntimeError("agent failed")

    result = await evaluate_agent_run(
        {
            "topic": "Phase 7",
            "expected_keywords": ["evaluation"],
            "max_iterations": 3,
            "mode": "agent",
        },
        run_fn,
    )

    assert result["completed"] is False
    assert result["keyword_coverage"] == 0.0
    assert result["error"] == "agent failed"


@pytest.mark.asyncio
async def test_evaluate_agent_run_does_not_forward_mode_keyword() -> None:
    captured: dict[str, object] = {}

    async def run_fn(topic: str, max_iterations: int, top_k: int) -> dict[str, object]:
        captured["topic"] = topic
        captured["max_iterations"] = max_iterations
        captured["top_k"] = top_k
        return {
            "report": "Phase 7 adds evaluation.",
            "iterations_used": 1,
            "search_result_count": 1,
        }

    result = await evaluate_agent_run(
        {
            "topic": "Phase 7",
            "expected_keywords": ["evaluation"],
            "max_iterations": 2,
            "mode": "agent_v2",
        },
        run_fn,
        top_k=4,
    )

    assert result["completed"] is True
    assert captured == {
        "topic": "Phase 7",
        "max_iterations": 2,
        "top_k": 4,
    }


@pytest.mark.asyncio
async def test_evaluate_batch_aggregates_metrics() -> None:
    async def run_fn(**kwargs: object) -> dict[str, object]:
        return {
            "report": f"{kwargs['topic']} evaluation",
            "iterations_used": 1,
            "search_result_count": 2,
        }

    result = await evaluate_agent_batch(
        [
            {"topic": "one", "expected_keywords": ["evaluation"], "max_iterations": 2, "mode": "agent"},
            {"topic": "two", "expected_keywords": ["missing"], "max_iterations": 2, "mode": "agent"},
        ],
        run_fn,
    )

    assert result["total"] == 2
    assert result["completed_count"] == 2
    assert result["success_rate"] == 0.5
    assert result["avg_iterations"] == 1.0
    assert len(result["per_case"]) == 2

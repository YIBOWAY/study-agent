from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict


class AgentEvalCase(TypedDict):
    topic: str
    expected_keywords: list[str]
    max_iterations: int
    mode: str


RunFn = Callable[..., Awaitable[dict[str, Any]]]


async def evaluate_agent_run(
    case: AgentEvalCase,
    run_fn: RunFn,
    **run_kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = await run_fn(
            topic=case["topic"],
            max_iterations=case["max_iterations"],
            **run_kwargs,
        )
        latency = time.perf_counter() - started
        report = str(result.get("report") or "")
        return {
            "topic": case["topic"],
            "mode": case["mode"],
            "report": report,
            "iterations_used": int(result.get("iterations_used") or 0),
            "search_count": _search_count(result),
            "keyword_coverage": _keyword_coverage(report, case["expected_keywords"]),
            "latency_seconds": latency,
            "completed": True,
            "error": "",
        }
    except Exception as exc:
        latency = time.perf_counter() - started
        return {
            "topic": case["topic"],
            "mode": case["mode"],
            "report": "",
            "iterations_used": 0,
            "search_count": 0,
            "keyword_coverage": 0.0,
            "latency_seconds": latency,
            "completed": False,
            "error": str(exc),
        }


async def evaluate_agent_batch(
    cases: list[AgentEvalCase],
    run_fn: RunFn,
    **run_kwargs: Any,
) -> dict[str, Any]:
    per_case = [
        await evaluate_agent_run(case, run_fn, **run_kwargs)
        for case in cases
    ]
    if not per_case:
        return {
            "total": 0,
            "completed_count": 0,
            "success_rate": 0.0,
            "avg_iterations": 0.0,
            "avg_latency": 0.0,
            "per_case": [],
        }

    completed_count = sum(1 for item in per_case if item["completed"])
    success_count = sum(
        1
        for item in per_case
        if item["completed"] and item["keyword_coverage"] >= 0.5
    )
    return {
        "total": len(per_case),
        "completed_count": completed_count,
        "success_rate": success_count / len(per_case),
        "avg_iterations": sum(item["iterations_used"] for item in per_case) / len(per_case),
        "avg_latency": sum(item["latency_seconds"] for item in per_case) / len(per_case),
        "per_case": per_case,
    }


def _keyword_coverage(report: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    lowered_report = report.lower()
    hits = sum(1 for keyword in expected_keywords if keyword.lower() in lowered_report)
    return hits / len(expected_keywords)


def _search_count(result: dict[str, Any]) -> int:
    if "search_result_count" in result:
        return int(result.get("search_result_count") or 0)
    search_results = result.get("search_results")
    return len(search_results) if isinstance(search_results, list) else 0

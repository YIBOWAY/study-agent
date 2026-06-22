from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.services.multi_agent.graph import (
    build_multi_agent_graph,
    build_multi_agent_initial_state,
)
from app.services.research.agent import build_agent_graph, build_agent_initial_state
from app.services.research.agent_v2 import (
    build_agent_v2_graph,
    build_agent_v2_initial_state,
)
from app.services.research.workflow import (
    build_workflow_graph,
    build_workflow_initial_state,
)

_APPEND_LIST_FIELDS = {"queries", "search_results", "steps"}


def _merge_state(state: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.items():
        if key in _APPEND_LIST_FIELDS and isinstance(state.get(key), list) and isinstance(value, list):
            state[key] = [*state[key], *value]
            continue
        state[key] = value


def _summarize_update(update: dict[str, Any]) -> str:
    steps = update.get("steps")
    if isinstance(steps, list) and steps:
        parts = [
            str(step.get("output_summary") or step.get("action") or "").strip()
            for step in steps
            if isinstance(step, dict)
        ]
        parts = [part for part in parts if part]
        if parts:
            return " | ".join(parts)[:200]

    changed_fields = [key for key in update if key != "steps"]
    if changed_fields:
        return f"updated: {', '.join(changed_fields)}"[:200]
    return "completed"


def _build_stream_result(mode: str, topic: str, state: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "topic": topic,
        "mode": mode,
        "report": state.get("report", ""),
        "queries": state.get("queries", []),
        "steps": state.get("steps", []),
        "iterations_used": state.get("iteration", 0),
        "search_result_count": len(state.get("search_results", [])),
    }
    if mode == "agent_v2":
        result["plan"] = state.get("plan", [])
        result["reflection_history"] = state.get("reflection", "")
        result["insights_used"] = len(state.get("prior_insights", []))
    if mode == "multi_agent":
        result["plan"] = state.get("plan", [])
        result["analysis"] = state.get("analysis", "")
        result["review_verdict"] = state.get("review_verdict", "")
        result["agents_involved"] = ["planner", "researcher", "analyst", "writer", "reviewer"]
    return result


def build_research_stream_runner(
    mode: str,
    *,
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: Any,
    llm_service: Any,
    tool_registry: Any,
    memory_service: Any,
    session_id: str,
) -> tuple[Any, dict[str, Any]]:
    if mode == "workflow":
        return (
            build_workflow_graph(rag_service, llm_service, tool_registry),
            build_workflow_initial_state(topic, max_iterations, top_k),
        )
    if mode == "agent":
        return (
            build_agent_graph(rag_service, llm_service, tool_registry),
            build_agent_initial_state(topic, max_iterations, top_k),
        )
    if mode == "agent_v2":
        return (
            build_agent_v2_graph(rag_service, llm_service, tool_registry, memory_service),
            build_agent_v2_initial_state(topic, max_iterations, top_k, session_id),
        )
    return (
        build_multi_agent_graph(rag_service, llm_service, tool_registry, memory_service),
        build_multi_agent_initial_state(topic, max_iterations, top_k, session_id),
    )


async def stream_research_events(
    mode: str,
    *,
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: Any,
    llm_service: Any,
    tool_registry: Any,
    memory_service: Any,
    session_id: str = "",
) -> AsyncIterator[dict[str, Any]]:
    compiled, state = build_research_stream_runner(
        mode,
        topic=topic,
        max_iterations=max_iterations,
        top_k=top_k,
        rag_service=rag_service,
        llm_service=llm_service,
        tool_registry=tool_registry,
        memory_service=memory_service,
        session_id=session_id,
    )
    try:
        async for chunk in compiled.astream(state, stream_mode="updates"):
            for node, update in chunk.items():
                if not isinstance(update, dict):
                    continue
                _merge_state(state, update)
                yield {
                    "event": "node_completed",
                    "node": node,
                    "summary": _summarize_update(update),
                    "steps": update.get("steps", []),
                    "iteration": state.get("iteration", 0),
                }
        yield {
            "event": "completed",
            "result": _build_stream_result(mode, topic, state),
        }
    except Exception as exc:
        yield {
            "event": "error",
            "message": str(exc),
        }

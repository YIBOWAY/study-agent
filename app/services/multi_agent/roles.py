from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.services.multi_agent.state import MultiAgentState
from app.services.research.nodes import (
    _format_evidence,
    _safe_load_json,
    _step,
    make_refine_query_node,
    make_rewrite_query_node,
    make_search_node,
)

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry

NodeHandler = Callable[[MultiAgentState], Awaitable[dict[str, Any]]]

_ANALYST_PROMPT = (
    "You are a research analyst. Analyze the evidence and decide whether the topic can already "
    "be answered well. Return JSON only in the form "
    "{\"analysis\": \"...\", \"evaluation\": \"sufficient\"|\"needs_more\", \"key_findings\": [\"...\"]}."
)
_WRITER_PROMPT = (
    "You are a professional research writer. Write or revise a structured research report using "
    "the analysis and evidence. Include: Title, Executive Summary, Key Findings, Sources, Conclusion."
)
_REVIEWER_PROMPT = (
    "You are a senior research reviewer. Evaluate the report for accuracy, completeness, clarity, "
    "and source grounding. Return JSON only in the form "
    "{\"verdict\": \"approved\"|\"needs_revision\", \"feedback\": \"...\"}."
)


def make_researcher_node(
    llm_service: "LLMService",
    rag_service: "RAGService",
    tool_registry: "ToolRegistry",
) -> NodeHandler:
    rewrite_node = make_rewrite_query_node(llm_service)
    refine_node = make_refine_query_node(llm_service)
    search_node = make_search_node(rag_service, tool_registry)

    async def researcher(state: MultiAgentState) -> dict[str, Any]:
        query_update = await (rewrite_node(state) if not state["queries"] else refine_node(state))
        merged_state = dict(state)
        if query_update.get("queries"):
            merged_state["queries"] = list(state["queries"]) + list(query_update["queries"])
        if "current_step" in query_update:
            merged_state["current_step"] = query_update["current_step"]
        search_update = await search_node(merged_state)
        steps = [_step("researcher", "Completed researcher cycle", f"iteration {search_update['iteration']}")]
        steps.extend(query_update.get("steps", []))
        steps.extend(search_update.get("steps", []))
        payload: dict[str, Any] = {
            "steps": steps,
            "search_results": search_update["search_results"],
            "iteration": search_update["iteration"],
            "current_phase": "analysis",
        }
        if query_update.get("queries"):
            payload["queries"] = query_update["queries"]
        if "current_step" in query_update:
            payload["current_step"] = query_update["current_step"]
        return payload

    return researcher


def make_analyst_node(llm_service: "LLMService") -> NodeHandler:
    async def analyst(state: MultiAgentState) -> dict[str, Any]:
        prompt = (
            f"Topic: {state['topic']}\n"
            f"Current step: {state.get('current_step', '')}\n"
            f"Prior insights: {state.get('prior_insights', [])}\n\n"
            f"Evidence:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_ANALYST_PROMPT)
            parsed = _safe_load_json(result["reply"])
            analysis = str(parsed.get("analysis") or result["reply"]).strip()
            evaluation = str(parsed.get("evaluation") or "needs_more").strip().lower()
            if evaluation not in {"sufficient", "needs_more"}:
                evaluation = "needs_more"
        except Exception as exc:
            analysis = str(exc)
            evaluation = "needs_more"
        return {
            "analysis": analysis,
            "evaluation": evaluation,
            "current_phase": "writing" if evaluation == "sufficient" else "research",
            "steps": [_step("analyst", "Analyzed evidence", f"{evaluation}: {analysis}")],
        }

    return analyst


def make_writer_node(llm_service: "LLMService") -> NodeHandler:
    async def writer(state: MultiAgentState) -> dict[str, Any]:
        is_revision = bool(state.get("review_feedback"))
        prompt = (
            f"Topic: {state['topic']}\n"
            f"Plan: {state['plan']}\n"
            f"Current step: {state.get('current_step', '')}\n"
            f"Analysis:\n{state.get('analysis', '')}\n\n"
            f"Review feedback:\n{state.get('review_feedback', '')}\n\n"
            f"Current report:\n{state.get('report', '')}\n\n"
            f"Evidence:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_WRITER_PROMPT)
            report = result["reply"].strip()
        except Exception as exc:
            report = state.get("report", "")
            return {
                "report": report,
                "steps": [_step("writer", "Writer failed", str(exc))],
            }

        payload: dict[str, Any] = {
            "report": report,
            "current_phase": "review",
            "steps": [
                _step(
                    "writer",
                    "Revised report" if is_revision else "Drafted report",
                    f"report length {len(report)}",
                )
            ],
        }
        if is_revision:
            payload["revision_count"] = state["revision_count"] + 1
        return payload

    return writer


def make_reviewer_node(llm_service: "LLMService") -> NodeHandler:
    async def reviewer(state: MultiAgentState) -> dict[str, Any]:
        prompt = (
            f"Topic: {state['topic']}\n\n"
            f"Report:\n{state.get('report', '')}\n\n"
            f"Evidence:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_REVIEWER_PROMPT)
            parsed = _safe_load_json(result["reply"])
            verdict = str(parsed.get("verdict") or "approved").strip().lower()
            feedback = str(parsed.get("feedback") or "").strip()
            if verdict not in {"approved", "needs_revision"}:
                verdict = "approved"
        except Exception as exc:
            verdict = "approved"
            feedback = str(exc)
        return {
            "review_verdict": verdict,
            "review_feedback": feedback,
            "current_phase": "done" if verdict == "approved" else "writing",
            "steps": [_step("reviewer", "Reviewed report", f"{verdict}: {feedback}")],
        }

    return reviewer


def route_after_analysis(state: MultiAgentState) -> str:
    if state["iteration"] >= state["max_iterations"]:
        return "write"
    if state["evaluation"] == "sufficient":
        return "write"
    return "research_more"


def route_after_review(state: MultiAgentState) -> str:
    if state["review_verdict"] == "approved":
        return "save"
    if state["revision_count"] >= 1:
        return "save"
    return "revise"

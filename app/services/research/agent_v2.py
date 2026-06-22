from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from app.services.research.nodes import (
    make_evaluate_results_node,
    make_generate_report_node,
    make_plan_node,
    make_recall_memory_node,
    make_refine_query_node,
    make_reflect_node,
    make_revise_report_node,
    make_rewrite_query_node,
    make_save_memory_node,
    make_search_node,
)
from app.services.research.state import ResearchState

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.memory_service import MemoryService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry


def _route_after_evaluation(state: ResearchState) -> str:
    if state["iteration"] >= state["max_iterations"]:
        return "sufficient"
    if state["evaluation"] == "sufficient":
        return "sufficient"
    return "needs_more"


def _route_after_reflection(state: ResearchState) -> str:
    if state.get("reflection") == "pass":
        return "pass"
    return "revise"


def build_agent_v2_graph(
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
    memory_service: "MemoryService",
):
    graph = StateGraph(ResearchState)
    graph.add_node("recall_memory", make_recall_memory_node(memory_service))
    graph.add_node("plan", make_plan_node(llm_service))
    graph.add_node("rewrite_query", make_rewrite_query_node(llm_service))
    graph.add_node("search", make_search_node(rag_service, tool_registry))
    graph.add_node("evaluate_results", make_evaluate_results_node(llm_service))
    graph.add_node("refine_query", make_refine_query_node(llm_service))
    graph.add_node("generate_report", make_generate_report_node(llm_service))
    graph.add_node("reflect", make_reflect_node(llm_service))
    graph.add_node("revise_report", make_revise_report_node(llm_service))
    graph.add_node("save_memory", make_save_memory_node(memory_service))

    graph.add_edge(START, "recall_memory")
    graph.add_edge("recall_memory", "plan")
    graph.add_edge("plan", "rewrite_query")
    graph.add_edge("rewrite_query", "search")
    graph.add_edge("search", "evaluate_results")
    graph.add_conditional_edges(
        "evaluate_results",
        _route_after_evaluation,
        {
            "sufficient": "generate_report",
            "needs_more": "refine_query",
        },
    )
    graph.add_edge("refine_query", "search")
    graph.add_edge("generate_report", "reflect")
    graph.add_conditional_edges(
        "reflect",
        _route_after_reflection,
        {
            "pass": "save_memory",
            "revise": "revise_report",
        },
    )
    graph.add_edge("revise_report", "save_memory")
    graph.add_edge("save_memory", END)
    return graph.compile()


def build_agent_v2_initial_state(topic: str, max_iterations: int, top_k: int, session_id: str) -> ResearchState:
    return {
        "topic": topic,
        "queries": [],
        "search_results": [],
        "report": "",
        "steps": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "evaluation": "",
        "top_k": top_k,
        "plan": [],
        "current_step": "",
        "reflection": "",
        "session_id": session_id,
        "prior_insights": [],
    }


async def run_agent_v2(
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
    memory_service: "MemoryService",
    session_id: str = "",
) -> dict[str, Any]:
    compiled = build_agent_v2_graph(rag_service, llm_service, tool_registry, memory_service)
    result = await compiled.ainvoke(build_agent_v2_initial_state(topic, max_iterations, top_k, session_id))
    return {
        "report": result["report"],
        "steps": result["steps"],
        "queries": result["queries"],
        "iterations_used": result["iteration"],
        "search_result_count": len(result["search_results"]),
        "plan": result.get("plan", []),
        "reflection_history": result.get("reflection", ""),
        "insights_used": len(result.get("prior_insights", [])),
    }

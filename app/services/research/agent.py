from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from app.services.research.nodes import (
    make_evaluate_results_node,
    make_generate_report_node,
    make_refine_query_node,
    make_rewrite_query_node,
    make_search_node,
)
from app.services.research.state import ResearchState

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry


def _route_after_evaluation(state: ResearchState) -> str:
    if state["iteration"] >= state["max_iterations"]:
        return "sufficient"
    if state["evaluation"] == "sufficient":
        return "sufficient"
    return "needs_more"


def build_agent_graph(
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
):
    graph = StateGraph(ResearchState)
    graph.add_node("rewrite_query", make_rewrite_query_node(llm_service))
    graph.add_node("search", make_search_node(rag_service, tool_registry))
    graph.add_node("evaluate_results", make_evaluate_results_node(llm_service))
    graph.add_node("refine_query", make_refine_query_node(llm_service))
    graph.add_node("generate_report", make_generate_report_node(llm_service))
    graph.add_edge(START, "rewrite_query")
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
    graph.add_edge("generate_report", END)
    return graph.compile()


def build_agent_initial_state(topic: str, max_iterations: int, top_k: int) -> ResearchState:
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
    }


async def run_agent(
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
) -> dict[str, Any]:
    compiled = build_agent_graph(rag_service, llm_service, tool_registry)
    result = await compiled.ainvoke(build_agent_initial_state(topic, max_iterations, top_k))
    return {
        "report": result["report"],
        "steps": result["steps"],
        "queries": result["queries"],
        "iterations_used": result["iteration"],
        "search_result_count": len(result["search_results"]),
    }

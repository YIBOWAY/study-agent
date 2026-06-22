from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from app.services.research.nodes import (
    make_generate_report_node,
    make_rewrite_query_node,
    make_search_node,
)
from app.services.research.state import ResearchState

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry


def build_workflow_graph(
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
):
    graph = StateGraph(ResearchState)
    graph.add_node("rewrite_query", make_rewrite_query_node(llm_service))
    graph.add_node("search", make_search_node(rag_service, tool_registry))
    graph.add_node("generate_report", make_generate_report_node(llm_service))
    graph.add_edge(START, "rewrite_query")
    graph.add_edge("rewrite_query", "search")
    graph.add_edge("search", "generate_report")
    graph.add_edge("generate_report", END)
    return graph.compile()


def build_workflow_initial_state(topic: str, max_iterations: int, top_k: int) -> ResearchState:
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


async def run_workflow(
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
) -> dict[str, Any]:
    compiled = build_workflow_graph(rag_service, llm_service, tool_registry)
    result = await compiled.ainvoke(build_workflow_initial_state(topic, max_iterations, top_k))
    return {
        "report": result["report"],
        "steps": result["steps"],
        "queries": result["queries"],
        "iterations_used": result["iteration"],
        "search_result_count": len(result["search_results"]),
    }

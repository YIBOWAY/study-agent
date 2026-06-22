from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from app.services.multi_agent.roles import (
    make_analyst_node,
    make_researcher_node,
    make_reviewer_node,
    make_writer_node,
    route_after_analysis,
    route_after_review,
)
from app.services.multi_agent.state import MultiAgentState
from app.services.research.nodes import (
    make_plan_node,
    make_recall_memory_node,
    make_save_memory_node,
)

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.memory_service import MemoryService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry


def build_multi_agent_graph(
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
    memory_service: "MemoryService | None" = None,
):
    graph = StateGraph(MultiAgentState)
    if memory_service is None:
        graph.add_node(
            "recall_memory",
            lambda state: {"prior_insights": [], "steps": []},
        )
        graph.add_node("save_memory", lambda state: {"steps": []})
    else:
        graph.add_node("recall_memory", make_recall_memory_node(memory_service))
        graph.add_node("save_memory", make_save_memory_node(memory_service))
    graph.add_node("plan_research", make_plan_node(llm_service))
    graph.add_node("researcher", make_researcher_node(llm_service, rag_service, tool_registry))
    graph.add_node("analyst", make_analyst_node(llm_service))
    graph.add_node("writer", make_writer_node(llm_service))
    graph.add_node("reviewer", make_reviewer_node(llm_service))

    graph.add_edge(START, "recall_memory")
    graph.add_edge("recall_memory", "plan_research")
    graph.add_edge("plan_research", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_conditional_edges(
        "analyst",
        route_after_analysis,
        {
            "write": "writer",
            "research_more": "researcher",
        },
    )
    graph.add_edge("writer", "reviewer")
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "save": "save_memory",
            "revise": "writer",
        },
    )
    graph.add_edge("save_memory", END)
    return graph.compile()


def build_multi_agent_initial_state(
    topic: str,
    max_iterations: int,
    top_k: int,
    session_id: str,
) -> MultiAgentState:
    return {
        "topic": topic,
        "queries": [],
        "search_results": [],
        "report": "",
        "steps": [],
        "plan": [],
        "current_step": "",
        "current_phase": "research",
        "iteration": 0,
        "max_iterations": max_iterations,
        "top_k": top_k,
        "analysis": "",
        "evaluation": "",
        "review_verdict": "",
        "review_feedback": "",
        "revision_count": 0,
        "session_id": session_id,
        "prior_insights": [],
    }


async def run_multi_agent(
    topic: str,
    max_iterations: int,
    top_k: int,
    rag_service: "RAGService",
    llm_service: "LLMService",
    tool_registry: "ToolRegistry",
    memory_service: "MemoryService | None" = None,
    session_id: str = "",
) -> dict[str, Any]:
    compiled = build_multi_agent_graph(rag_service, llm_service, tool_registry, memory_service)
    result = await compiled.ainvoke(
        build_multi_agent_initial_state(topic, max_iterations, top_k, session_id)
    )

    return {
        "report": result["report"],
        "steps": result["steps"],
        "queries": result["queries"],
        "iterations_used": result["iteration"],
        "search_result_count": len(result["search_results"]),
        "plan": result["plan"],
        "analysis": result.get("analysis", ""),
        "review_verdict": result.get("review_verdict", ""),
        "agents_involved": ["planner", "researcher", "analyst", "writer", "reviewer"],
    }

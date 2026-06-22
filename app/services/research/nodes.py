from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.services.research.state import ResearchSearchResult, ResearchState, ResearchStep

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
    from app.services.memory_service import MemoryService
    from app.services.rag_service import RAGService
    from app.services.tool_registry import ToolRegistry

NodeHandler = Callable[[ResearchState], Awaitable[dict[str, Any]]]

_QUERY_REWRITE_PROMPT = (
    "You are a search query optimizer. Given a research topic, rewrite it into a concise, "
    "specific search query optimized for semantic search. Return ONLY the query, no explanation."
)
_EVALUATION_PROMPT = (
    "You evaluate whether search results are sufficient to answer a research topic. "
    "Return JSON only in the form {\"evaluation\": \"sufficient\"|\"needs_more\", \"reason\": \"...\"}."
)
_REFINE_PROMPT = (
    "You refine a research search query from a different angle. Avoid repeating prior queries. "
    "Return ONLY the new query text."
)
_REPORT_PROMPT = (
    "You are a research assistant. Produce a structured report with sections: Title, Summary, "
    "Key Findings, Sources, Conclusion. Base the answer only on the provided evidence."
)
_PLAN_PROMPT = (
    "You are a research planner. Break the topic into 2-4 specific sub-questions that would "
    "cover the topic well. Return JSON only in the form "
    "{\"sub_tasks\": [\"question 1\", \"question 2\"]}."
)
_REFLECT_PROMPT = (
    "You are a research report reviewer. Evaluate the report for completeness, accuracy, clarity, "
    "and coverage. Return JSON only in the form "
    "{\"verdict\": \"pass\"|\"revise\", \"feedback\": \"...\"}."
)
_REVISE_REPORT_PROMPT = (
    "You are a research report editor. Revise the report based on the review feedback while "
    "keeping the same overall structure and grounding the changes in the provided evidence."
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _step(node: str, action: str, output_summary: str) -> ResearchStep:
    return {
        "node": node,
        "action": action,
        "output_summary": output_summary[:200],
        "timestamp": _timestamp(),
    }


def make_rewrite_query_node(llm_service: "LLMService") -> NodeHandler:
    async def rewrite_query(state: ResearchState) -> dict[str, Any]:
        user_message = _build_rewrite_query_prompt(state)
        try:
            result = await llm_service.chat(user_message, system_prompt=_QUERY_REWRITE_PROMPT)
            query = result["reply"].strip() or state["topic"].strip()
            payload: dict[str, Any] = {
                "queries": [query],
                "steps": [_step("rewrite_query", "Rewrote topic to search query", query)],
            }
            current_step = state.get("current_step")
            if current_step:
                payload["current_step"] = current_step
            return payload
        except Exception as exc:
            fallback = state["topic"].strip()
            return {
                "queries": [fallback],
                "steps": [_step("rewrite_query", "Query rewrite failed", str(exc))],
            }

    return rewrite_query


def make_search_node(
    rag_service: "RAGService",
    tool_registry: "ToolRegistry",
) -> NodeHandler:
    async def search(state: ResearchState) -> dict[str, Any]:
        query = state["queries"][-1]
        top_k = state["top_k"]
        kb_results: list[ResearchSearchResult] = []
        web_results: list[ResearchSearchResult] = []
        kb_step: ResearchStep | None = None
        web_step: ResearchStep | None = None

        async def search_knowledge_base() -> None:
            nonlocal kb_results, kb_step
            try:
                rag_result = await rag_service.search(query=query, top_k=top_k)
                items = rag_result.get("results", [])
                kb_results = [
                    _normalize_kb_result(item, query)
                    for item in items
                ]
                kb_step = _step(
                    "search_knowledge_base",
                    "Searched local knowledge base",
                    f"Found {len(kb_results)} results",
                )
            except Exception as exc:
                kb_step = _step("search_knowledge_base", "Knowledge base search failed", str(exc))

        async def search_web() -> None:
            nonlocal web_results, web_step
            if not tool_registry.settings.tavily_api_key:
                web_step = _step("web_search", "Skipped web search", "Tavily API key is not configured")
                return
            record = await tool_registry.execute(
                "web_search",
                {"query": query, "max_results": min(top_k, 10)},
            )
            if record.error:
                web_step = _step("web_search", "Web search failed", record.error)
                return

            web_results = _parse_web_search_results(record.result, query)
            web_step = _step(
                "web_search",
                "Searched the web",
                f"Found {len(web_results)} results",
            )

        await asyncio.gather(search_knowledge_base(), search_web())
        ordered_steps = [step for step in (kb_step, web_step) if step is not None]
        return {
            "search_results": kb_results + web_results,
            "steps": ordered_steps,
            "iteration": state["iteration"] + 1,
        }

    return search


def make_evaluate_results_node(llm_service: "LLMService") -> NodeHandler:
    async def evaluate_results(state: ResearchState) -> dict[str, Any]:
        if state["iteration"] >= state["max_iterations"]:
            return {
                "evaluation": "sufficient",
                "steps": [_step("evaluate_results", "Reached max iterations", "forcing sufficient")],
            }

        evidence = _format_evidence(state)
        prompt = f"Topic: {state['topic']}\n\nEvidence:\n{evidence}"
        try:
            result = await llm_service.chat(prompt, system_prompt=_EVALUATION_PROMPT)
            parsed = _safe_load_json(result["reply"])
            evaluation = str(parsed.get("evaluation") or "needs_more")
            if evaluation not in {"sufficient", "needs_more"}:
                evaluation = "needs_more"
            reason = str(parsed.get("reason") or "")
            return {
                "evaluation": evaluation,
                "steps": [_step("evaluate_results", "Evaluated search results", f"{evaluation}: {reason}")],
            }
        except Exception as exc:
            return {
                "evaluation": "needs_more",
                "steps": [_step("evaluate_results", "Evaluation failed", str(exc))],
            }

    return evaluate_results


def make_refine_query_node(llm_service: "LLMService") -> NodeHandler:
    async def refine_query(state: ResearchState) -> dict[str, Any]:
        next_step = _next_plan_step(state)
        prompt = (
            f"Topic: {state['topic']}\n"
            f"Current plan step: {next_step or state.get('current_step', '')}\n"
            f"Previous queries: {state['queries']}\n"
            f"Prior insights: {state.get('prior_insights', [])}\n"
            f"Evidence so far:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_REFINE_PROMPT)
            query = result["reply"].strip() or state["topic"].strip()
            payload: dict[str, Any] = {
                "queries": [query],
                "steps": [_step("refine_query", "Generated refined query", query)],
            }
            if next_step:
                payload["current_step"] = next_step
            return payload
        except Exception as exc:
            return {
                "steps": [_step("refine_query", "Query refinement failed", str(exc))],
            }

    return refine_query


def make_generate_report_node(llm_service: "LLMService") -> NodeHandler:
    async def generate_report(state: ResearchState) -> dict[str, Any]:
        prompt = f"Topic: {state['topic']}\n\nEvidence:\n{_format_evidence(state)}"
        try:
            result = await llm_service.chat(prompt, system_prompt=_REPORT_PROMPT)
            report = result["reply"].strip()
            return {
                "report": report,
                "steps": [
                    _step(
                        "generate_report",
                        "Generated research report",
                        f"Report generated ({len(report)} chars)",
                    )
                ],
            }
        except Exception as exc:
            return {
                "report": "",
                "steps": [_step("generate_report", "Report generation failed", str(exc))],
            }

    return generate_report


def make_plan_node(llm_service: "LLMService") -> NodeHandler:
    async def plan(state: ResearchState) -> dict[str, Any]:
        prompt = (
            f"Topic: {state['topic']}\n"
            f"Prior insights: {state.get('prior_insights', [])}\n"
            "Return 2-4 sub_tasks that would guide the research."
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_PLAN_PROMPT)
            parsed = _safe_load_json(result["reply"])
            raw_tasks = parsed.get("sub_tasks")
            tasks = [str(item).strip() for item in raw_tasks] if isinstance(raw_tasks, list) else []
            tasks = [item for item in tasks if item]
            if not tasks:
                raise ValueError("No valid sub_tasks returned.")
        except Exception as exc:
            fallback = state["topic"].strip()
            return {
                "plan": [fallback],
                "current_step": fallback,
                "steps": [_step("plan", "Planning failed; using fallback plan", str(exc))],
            }

        return {
            "plan": tasks,
            "current_step": tasks[0],
            "steps": [_step("plan", "Generated research plan", f"{len(tasks)} sub-tasks")],
        }

    return plan


def make_reflect_node(llm_service: "LLMService") -> NodeHandler:
    async def reflect(state: ResearchState) -> dict[str, Any]:
        prompt = (
            f"Topic: {state['topic']}\n\n"
            f"Report:\n{state.get('report', '')}\n\n"
            f"Evidence:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_REFLECT_PROMPT)
            parsed = _safe_load_json(result["reply"])
            verdict = str(parsed.get("verdict") or "pass").strip().lower()
            feedback = str(parsed.get("feedback") or "").strip()
            if verdict == "revise":
                reflection = feedback or "Revise the report."
            else:
                reflection = "pass"
        except Exception as exc:
            reflection = "pass"
            feedback = str(exc)
        return {
            "reflection": reflection,
            "steps": [
                _step(
                    "reflect",
                    "Reviewed generated report",
                    reflection if reflection != "pass" else feedback or "pass",
                )
            ],
        }

    return reflect


def make_revise_report_node(llm_service: "LLMService") -> NodeHandler:
    async def revise_report(state: ResearchState) -> dict[str, Any]:
        prompt = (
            f"Topic: {state['topic']}\n\n"
            f"Original report:\n{state.get('report', '')}\n\n"
            f"Review feedback:\n{state.get('reflection', '')}\n\n"
            f"Evidence:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_REVISE_REPORT_PROMPT)
            report = result["reply"].strip()
            return {
                "report": report,
                "steps": [
                    _step(
                        "revise_report",
                        "Revised report from review feedback",
                        f"Report revised ({len(report)} chars)",
                    )
                ],
            }
        except Exception as exc:
            return {
                "steps": [_step("revise_report", "Report revision failed", str(exc))],
            }

    return revise_report


def make_recall_memory_node(memory_service: "MemoryService") -> NodeHandler:
    async def recall_memory(state: ResearchState) -> dict[str, Any]:
        session_id = str(state.get("session_id") or "").strip()
        if not session_id:
            return {
                "prior_insights": [],
                "steps": [_step("recall_memory", "Skipped memory recall", "No session_id provided")],
            }

        prior_insights: list[str] = []
        session = await memory_service.get_session_context(session_id)
        if session is not None:
            prior_insights.extend(str(item).strip() for item in session.get("insights", []) if str(item).strip())

        records = await memory_service.retrieve_relevant_insights(state["topic"], top_k=3)
        for record in records:
            insight = str(record.get("insight") or "").strip()
            if insight and insight not in prior_insights:
                prior_insights.append(insight)

        return {
            "prior_insights": prior_insights,
            "steps": [
                _step(
                    "recall_memory",
                    "Recalled prior memory",
                    f"Loaded {len(prior_insights)} prior insights",
                )
            ],
        }

    return recall_memory


def make_save_memory_node(memory_service: "MemoryService") -> NodeHandler:
    async def save_memory(state: ResearchState) -> dict[str, Any]:
        session_id = str(state.get("session_id") or "").strip()
        if not session_id:
            return {
                "steps": [_step("save_memory", "Skipped memory save", "No session_id provided")],
            }

        insight = state.get("report", "").strip()[:200].strip()
        if insight:
            await memory_service.save_insight(
                topic=state["topic"],
                insight=insight,
                source_count=len(state["search_results"]),
                session_id=session_id,
            )
            await memory_service.add_session_context(
                session_id=session_id,
                topic=state["topic"],
                insights=[insight],
            )
        return {
            "steps": [
                _step(
                    "save_memory",
                    "Saved memory after research run",
                    "Saved insight to session and long-term memory" if insight else "No insight to save",
                )
            ],
        }

    return save_memory


def _format_evidence(state: ResearchState) -> str:
    lines: list[str] = []
    for index, item in enumerate(state["search_results"], start=1):
        title = item.get("title") or item.get("source") or "result"
        url = item.get("url") or ""
        snippet = item.get("text_snippet") or ""
        lines.append(f"[{index}] {title}")
        if url:
            lines.append(f"URL: {url}")
        lines.append(f"Snippet: {snippet}")
    return "\n".join(lines).strip()


def _normalize_kb_result(item: object, query: str) -> ResearchSearchResult:
    if isinstance(item, dict):
        text = item.get("text")
        score = item.get("score")
        source_name = item.get("source_name")
    else:
        text = getattr(item, "text", "")
        score = getattr(item, "score", 0.0)
        source_name = getattr(item, "source_name", "knowledge_base")

    return {
        "source": "knowledge_base",
        "query": query,
        "text_snippet": str(text or ""),
        "score": float(score or 0.0),
        "title": str(source_name or "knowledge_base"),
        "url": None,
    }


def _parse_web_search_results(result: str, query: str) -> list[ResearchSearchResult]:
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    parsed: list[ResearchSearchResult] = []
    title = ""
    url: str | None = None
    snippet = ""
    for line in lines:
        if line.startswith("[") and "] " in line:
            if title or snippet:
                parsed.append(
                    {
                        "source": "web",
                        "query": query,
                        "text_snippet": snippet,
                        "score": 0.0,
                        "title": title or "web result",
                        "url": url,
                    }
                )
            title = line.split("] ", 1)[1]
            url = None
            snippet = ""
            continue
        if line.startswith("URL: "):
            url = line[5:].strip() or None
            continue
        if line.startswith("Content: "):
            snippet = line[9:].strip()

    if title or snippet:
        parsed.append(
            {
                "source": "web",
                "query": query,
                "text_snippet": snippet,
                "score": 0.0,
                "title": title or "web result",
                "url": url,
            }
        )
    return parsed


def _safe_load_json(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _build_rewrite_query_prompt(state: ResearchState) -> str:
    current_step = str(state.get("current_step") or "").strip()
    prior_insights = state.get("prior_insights", [])
    if not current_step and not prior_insights:
        return state["topic"]
    return (
        f"Topic: {state['topic']}\n"
        f"Current plan step: {current_step}\n"
        f"Prior insights: {prior_insights}\n"
        "Write the best next search query."
    )


def _next_plan_step(state: ResearchState) -> str:
    plan = state.get("plan", [])
    if not plan:
        return ""
    iteration = int(state.get("iteration", 0))
    if iteration < len(plan):
        return str(plan[iteration])
    return ""

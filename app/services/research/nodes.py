from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from app.services.research.state import ResearchSearchResult, ResearchState, ResearchStep

if TYPE_CHECKING:
    from app.services.llm_service import LLMService
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
        try:
            result = await llm_service.chat(state["topic"], system_prompt=_QUERY_REWRITE_PROMPT)
            query = result["reply"].strip() or state["topic"].strip()
            return {
                "queries": [query],
                "steps": [_step("rewrite_query", "Rewrote topic to search query", query)],
            }
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
        prompt = (
            f"Topic: {state['topic']}\n"
            f"Previous queries: {state['queries']}\n"
            f"Evidence so far:\n{_format_evidence(state)}"
        )
        try:
            result = await llm_service.chat(prompt, system_prompt=_REFINE_PROMPT)
            query = result["reply"].strip() or state["topic"].strip()
            return {
                "queries": [query],
                "steps": [_step("refine_query", "Generated refined query", query)],
            }
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

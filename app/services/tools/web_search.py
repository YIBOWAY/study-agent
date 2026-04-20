from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


_ALLOWED_SEARCH_DEPTHS = {"basic", "advanced"}
_ALLOWED_TOPICS = {"general", "news", "finance"}
_DEFAULT_MAX_RESULTS = 5
_MAX_RESULTS_LIMIT = 10
_SNIPPET_LIMIT = 300


class WebSearchTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(self, arguments: dict[str, Any]) -> str:
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")
        if not self.settings.tavily_api_key:
            raise ValueError("Tavily API key is not configured.")

        max_results = self._parse_max_results(arguments.get("max_results", _DEFAULT_MAX_RESULTS))
        search_depth = self._parse_search_depth(arguments.get("search_depth", "basic"))
        topic = self._parse_topic(arguments.get("topic", "general"))

        url = f"{self.settings.tavily_base_url.rstrip('/')}/search"
        headers = {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.tool_call_timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ValueError(f"Failed to call Tavily API: {exc}") from exc

        if response.status_code >= 400:
            raise ValueError(
                f"Tavily API error ({response.status_code}): {self._extract_error_message(response)}"
            )

        data = self._parse_response_json(response)
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list) or not results:
            return "No web search results found."

        lines: list[str] = []
        for index, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Untitled result").strip()
            result_url = str(item.get("url") or "").strip() or "No URL"
            content = str(item.get("content") or "").replace("\n", " ").strip()
            lines.append(f"[{index}] {title}")
            lines.append(f"URL: {result_url}")
            lines.append(f"Content: {content[:_SNIPPET_LIMIT]}")
            lines.append("")

        formatted = "\n".join(lines).strip()
        return formatted or "No web search results found."

    @staticmethod
    def _parse_max_results(value: Any) -> int:
        try:
            max_results = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_results must be an integer between 1 and 10") from exc
        if max_results < 1 or max_results > _MAX_RESULTS_LIMIT:
            raise ValueError("max_results must be between 1 and 10")
        return max_results

    @staticmethod
    def _parse_search_depth(value: Any) -> str:
        search_depth = str(value or "basic").strip().lower()
        if search_depth not in _ALLOWED_SEARCH_DEPTHS:
            raise ValueError("search_depth must be one of: basic, advanced")
        return search_depth

    @staticmethod
    def _parse_topic(value: Any) -> str:
        topic = str(value or "general").strip().lower()
        if topic not in _ALLOWED_TOPICS:
            raise ValueError("topic must be one of: general, news, finance")
        return topic

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            text = response.text.strip()
            return text or "Unknown error"

        if isinstance(payload, dict):
            for key in ("detail", "error", "message"):
                value = payload.get(key)
                if value:
                    return str(value)
        return str(payload)

    @staticmethod
    def _parse_response_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid Tavily API response") from exc
        if not isinstance(payload, dict):
            raise ValueError("Invalid Tavily API response")
        return payload


def build_web_search_tool(settings: Settings) -> BuiltinTool:
    return BuiltinTool(
        name="web_search",
        description="Search the web for real-time information using Tavily Search API.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for the web.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to summarize.",
                    "default": _DEFAULT_MAX_RESULTS,
                },
                "search_depth": {
                    "type": "string",
                    "description": "Search depth to use.",
                    "enum": sorted(_ALLOWED_SEARCH_DEPTHS),
                    "default": "basic",
                },
                "topic": {
                    "type": "string",
                    "description": "Search topic to target.",
                    "enum": sorted(_ALLOWED_TOPICS),
                    "default": "general",
                },
            },
            "required": ["query"],
        },
        handler=WebSearchTool(settings),
    )

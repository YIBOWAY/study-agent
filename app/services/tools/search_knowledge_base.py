from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.rag_service import RAGService


@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


class KnowledgeBaseSearchTool:
    def __init__(self, rag_service: "RAGService") -> None:
        self.rag_service = rag_service

    async def __call__(self, arguments: dict[str, Any]) -> str:
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")

        top_k = int(arguments.get("top_k", 3))
        if top_k < 1 or top_k > 10:
            raise ValueError("top_k must be between 1 and 10")
        document_id = arguments.get("document_id")
        if document_id is not None:
            document_id = str(document_id)

        result = await self.rag_service.search(query=query, top_k=top_k, document_id=document_id)
        items = result["results"]
        if not items:
            return "No knowledge base results found."

        summary_lines = []
        for index, item in enumerate(items, start=1):
            snippet = item.text if hasattr(item, "text") else item.get("text", "")
            source_name = item.source_name if hasattr(item, "source_name") else item.get("source_name", "unknown")
            page_number = item.page_number if hasattr(item, "page_number") else item.get("page_number")
            snippet = str(snippet).replace("\n", " ").strip()
            snippet = snippet[:200]
            location = f" (page {page_number})" if page_number is not None else ""
            summary_lines.append(f"[{index}] {source_name}{location}: {snippet}")

        return "\n".join(summary_lines)


def build_search_knowledge_base_tool(rag_service: "RAGService") -> BuiltinTool:
    return BuiltinTool(
        name="search_knowledge_base",
        description="Search the project's knowledge base using the existing RAG retrieval pipeline.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for the knowledge base.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to summarize.",
                    "default": 3,
                },
                "document_id": {
                    "type": "string",
                    "description": "Optional document identifier to scope the search.",
                },
            },
            "required": ["query"],
        },
        handler=KnowledgeBaseSearchTool(rag_service),
    )

from __future__ import annotations

from app.core.config import Settings
from app.services.research.streaming import stream_research_events
from app.services.tool_registry import ToolRegistry


class FakeLLMService:
    def __init__(self) -> None:
        self.calls = 0

    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        self.calls += 1
        if self.calls == 1:
            return {"reply": "rag chunking impact", "model": "gpt-5.4"}
        return {"reply": "# Report\n\nSummary", "model": "gpt-5.4"}


class FakeRAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "source_name": "phase8.md",
                    "text": "Phase 8 adds streaming chat and deployment assets.",
                    "score": 0.9,
                }
            ],
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v3.5",
        }


async def test_stream_research_events_workflow_emits_node_updates() -> None:
    settings = Settings(
        tavily_api_key="",
        tracing_enabled=False,
        guardrails_enabled=False,
    )
    llm_service = FakeLLMService()
    rag_service = FakeRAGService()
    tool_registry = ToolRegistry(settings=settings, rag_service=rag_service)

    events = [
        event
        async for event in stream_research_events(
            "workflow",
            topic="What changed in Phase 8?",
            max_iterations=3,
            top_k=5,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
            memory_service=None,
        )
    ]

    assert [event["event"] for event in events] == [
        "node_completed",
        "node_completed",
        "node_completed",
        "completed",
    ]
    assert [events[index]["node"] for index in range(3)] == [
        "rewrite_query",
        "search",
        "generate_report",
    ]
    assert events[-1]["result"]["report"] == "# Report\n\nSummary"

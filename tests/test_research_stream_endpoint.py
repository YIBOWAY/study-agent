from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_guardrails_service, get_tracing_service
from app.main import app

client = TestClient(app)


async def _fake_research_stream() -> AsyncIterator[dict[str, object]]:
    yield {"event": "node_completed", "node": "rewrite_query", "summary": "query ready"}
    yield {"event": "node_completed", "node": "search", "summary": "3 results"}
    yield {"event": "completed", "result": {"report": "# Done"}}


def test_research_stream_endpoint_returns_sse(monkeypatch: Any) -> None:
    import app.api.routes.research as research_route

    app.dependency_overrides[get_guardrails_service] = lambda: None
    app.dependency_overrides[get_tracing_service] = lambda: None
    monkeypatch.setattr(
        research_route,
        "_stream_research_events",
        lambda *args, **kwargs: _fake_research_stream(),
    )
    try:
        with client.stream(
            "POST",
            "/api/v1/research?stream=true",
            json={"topic": "RAG chunking impact", "mode": "workflow"},
        ) as response:
            body = "".join(response.iter_text())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert '"node": "rewrite_query"' in body
    assert '"node": "search"' in body
    assert '"event": "completed"' in body
    assert "data: [DONE]" in body


def test_research_stream_endpoint_content_type_correct(monkeypatch: Any) -> None:
    import app.api.routes.research as research_route

    app.dependency_overrides[get_guardrails_service] = lambda: None
    app.dependency_overrides[get_tracing_service] = lambda: None
    monkeypatch.setattr(
        research_route,
        "_stream_research_events",
        lambda *args, **kwargs: _fake_research_stream(),
    )
    try:
        with client.stream(
            "POST",
            "/api/v1/research?stream=true",
            json={"topic": "RAG chunking impact", "mode": "workflow"},
        ) as response:
            _ = list(response.iter_text())
            content_type = response.headers["content-type"]
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert content_type.startswith("text/event-stream")

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_guardrails_service, get_tracing_service
from app.main import app

client = TestClient(app)


async def _fake_stream() -> AsyncIterator[str]:
    yield "Hello"
    yield " world"


def test_stream_endpoint_returns_sse(monkeypatch: Any) -> None:
    import app.api.routes.chat as chat_route

    app.dependency_overrides[get_guardrails_service] = lambda: None
    app.dependency_overrides[get_tracing_service] = lambda: None
    monkeypatch.setattr(chat_route.llm_service, "chat_stream", lambda *args, **kwargs: _fake_stream())
    try:
        with client.stream("POST", "/api/v1/chat/stream", json={"message": "stream please"}) as response:
            body = "".join(response.iter_text())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert 'data: {"content": "Hello"}' in body
    assert 'data: {"content": " world"}' in body
    assert "data: [DONE]" in body


def test_stream_endpoint_content_type_correct(monkeypatch: Any) -> None:
    import app.api.routes.chat as chat_route

    app.dependency_overrides[get_guardrails_service] = lambda: None
    app.dependency_overrides[get_tracing_service] = lambda: None
    monkeypatch.setattr(chat_route.llm_service, "chat_stream", lambda *args, **kwargs: _fake_stream())
    try:
        with client.stream("POST", "/api/v1/chat/stream", json={"message": "stream please"}) as response:
            _ = list(response.iter_text())
            content_type = response.headers["content-type"]
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert content_type.startswith("text/event-stream")

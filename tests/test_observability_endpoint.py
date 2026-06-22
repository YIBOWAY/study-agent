from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_tracing_service
from app.main import app

client = TestClient(app)


class FakeTracingService:
    async def query_traces(self, limit: int = 100, name: str | None = None) -> list[dict[str, Any]]:
        return [{"trace_id": "t1", "name": name or "llm_chat"}]

    async def get_cost_summary(self, since: str | None = None) -> dict[str, Any]:
        return {
            "total_cost_usd": 1.23,
            "total_calls": 2,
            "total_tokens": {"prompt": 10, "completion": 5},
            "by_model": {"gpt-5.4": {"calls": 2, "cost": 1.23, "tokens": {"prompt": 10, "completion": 5}}},
            "since": since or "",
        }

    async def query_agent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return [{"root": {"trace_id": "root-1", "name": "agent_run"}, "children": []}]


def test_get_traces_endpoint() -> None:
    app.dependency_overrides[get_tracing_service] = lambda: FakeTracingService()
    try:
        response = client.get("/api/v1/observability/traces?limit=5&name=llm_chat")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["traces"][0]["name"] == "llm_chat"


def test_get_cost_endpoint() -> None:
    app.dependency_overrides[get_tracing_service] = lambda: FakeTracingService()
    try:
        response = client.get("/api/v1/observability/cost?since=2026-05-01")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_cost_usd"] == 1.23
    assert response.json()["since"] == "2026-05-01"


def test_get_agent_runs_endpoint() -> None:
    app.dependency_overrides[get_tracing_service] = lambda: FakeTracingService()
    try:
        response = client.get("/api/v1/observability/agent_runs?limit=3")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["runs"][0]["root"]["name"] == "agent_run"

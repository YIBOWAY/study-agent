from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def _override_settings(*, required: bool, api_key: str = "secret-key") -> Settings:
    return Settings(
        api_key_required=required,
        api_key=api_key,
        tracing_enabled=False,
    )


def test_no_api_key_when_not_required() -> None:
    app.dependency_overrides[get_settings] = lambda: _override_settings(required=False)
    try:
        response = client.get("/api/v1/tools/list")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200


def test_api_key_required_blocks_missing_key() -> None:
    app.dependency_overrides[get_settings] = lambda: _override_settings(required=True)
    try:
        tool_response = client.get("/api/v1/tools/list")
        research_response = client.post(
            "/api/v1/research",
            json={"topic": "RAG chunking impact", "mode": "workflow"},
        )
        memory_response = client.get("/api/v1/memory/insights")
    finally:
        app.dependency_overrides.clear()

    assert tool_response.status_code == 401
    assert research_response.status_code == 401
    assert memory_response.status_code == 401


def test_api_key_required_accepts_valid_key() -> None:
    app.dependency_overrides[get_settings] = lambda: _override_settings(required=True)
    headers = {"X-API-Key": "secret-key"}
    try:
        response = client.get("/api/v1/tools/list", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.api.dependencies import get_guardrails_service
from app.main import app

client = TestClient(app)


class FakeMCPRuntime:
    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "filesystem",
                "tool_count": 1,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "mcp__filesystem__read_file",
                            "description": "Read a file.",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
            }
        ]

    def list_all_tools(self) -> list[dict[str, Any]]:
        return self.list_servers()[0]["tools"]

    async def execute_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if prefixed_name == "mcp__filesystem__error":
            return {"result": "failed", "is_error": True}
        return {"result": f"called {prefixed_name} with {arguments}", "is_error": False}


class AllowingGuardrails:
    def validate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, object]:
        return {"safe": True, "reason": "ok"}


class BlockingGuardrails:
    def validate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, object]:
        return {"safe": False, "reason": "blocked by test"}


def test_get_servers_when_runtime_not_initialized() -> None:
    response = client.get("/api/v1/mcp/servers")

    assert response.status_code == 200
    assert response.json() == {"servers": []}


def test_get_tools_endpoint(monkeypatch: Any) -> None:
    import app.api.routes.mcp as mcp_route

    monkeypatch.setattr(mcp_route, "get_mcp_runtime", lambda: FakeMCPRuntime())

    response = client.get("/api/v1/mcp/tools")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["tools"][0]["function"]["name"] == "mcp__filesystem__read_file"


def test_invoke_tool_endpoint_success(monkeypatch: Any) -> None:
    import app.api.routes.mcp as mcp_route

    monkeypatch.setattr(mcp_route, "get_mcp_runtime", lambda: FakeMCPRuntime())
    app.dependency_overrides[get_guardrails_service] = lambda: AllowingGuardrails()
    try:
        response = client.post(
            "/api/v1/mcp/tools/mcp__filesystem__read_file/invoke",
            json={"arguments": {"path": "/tmp/a.txt"}},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["is_error"] is False
    assert "mcp__filesystem__read_file" in response.json()["result"]


def test_invoke_tool_endpoint_error(monkeypatch: Any) -> None:
    import app.api.routes.mcp as mcp_route

    monkeypatch.setattr(mcp_route, "get_mcp_runtime", lambda: FakeMCPRuntime())
    app.dependency_overrides[get_guardrails_service] = lambda: AllowingGuardrails()
    try:
        response = client.post(
            "/api/v1/mcp/tools/mcp__filesystem__error/invoke",
            json={"arguments": {}},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"result": "failed", "is_error": True}


def test_invoke_tool_endpoint_guardrails_block(monkeypatch: Any) -> None:
    import app.api.routes.mcp as mcp_route

    monkeypatch.setattr(mcp_route, "get_mcp_runtime", lambda: FakeMCPRuntime())
    app.dependency_overrides[get_guardrails_service] = lambda: BlockingGuardrails()
    try:
        response = client.post(
            "/api/v1/mcp/tools/mcp__filesystem__read_file/invoke",
            json={"arguments": {"path": "/tmp/a.txt"}},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "blocked by test"

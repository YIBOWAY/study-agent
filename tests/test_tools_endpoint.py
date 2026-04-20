from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tools_list_endpoint_returns_registered_tools() -> None:
    response = client.get("/api/v1/tools/list")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["tools"]]
    assert names == [
        "get_current_time",
        "calculate",
        "search_knowledge_base",
        "web_search",
    ]


@patch("app.api.routes.tools.llm_service.chat_with_tools", new_callable=AsyncMock)
def test_tools_chat_endpoint_returns_response(mock_chat_with_tools: AsyncMock) -> None:
    mock_chat_with_tools.return_value = {
        "reply": "Beijing time is 2026-04-18 22:30:00 and 23 * 47 = 1081.",
        "model": "gpt-5.4",
        "tool_calls_made": [
            {
                "tool": "get_current_time",
                "args": {"timezone": "Asia/Shanghai"},
                "result": "2026-04-18 22:30:00 CST",
                "error": None,
            },
            {
                "tool": "calculate",
                "args": {"expression": "23 * 47"},
                "result": "1081",
                "error": None,
            },
        ],
    }

    response = client.post(
        "/api/v1/tools/chat",
        json={
            "message": "What time is it in Beijing and what is 23 * 47?",
            "enabled_tools": ["get_current_time", "calculate"],
            "max_iterations": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-5.4"
    assert response.json()["tool_calls_made"][1]["result"] == "1081"


@patch("app.api.routes.tools.llm_service.chat_with_tools", new_callable=AsyncMock)
def test_tools_chat_endpoint_returns_generic_error(mock_chat_with_tools: AsyncMock) -> None:
    mock_chat_with_tools.side_effect = RuntimeError("unexpected failure")

    response = client.post(
        "/api/v1/tools/chat",
        json={"message": "Use tools please"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to complete tool chat."


def test_tools_chat_endpoint_rejects_empty_message() -> None:
    response = client.post(
        "/api/v1/tools/chat",
        json={"message": ""},
    )

    assert response.status_code == 422

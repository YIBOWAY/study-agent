from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routes.chat.llm_service.extract", new_callable=AsyncMock)
def test_extract_endpoint_returns_structured_data(mock_extract: AsyncMock) -> None:
    mock_extract.return_value = {
        "summary": "这是一段摘要。",
        "keywords": ["Agent", "FastAPI"],
        "sentiment": "neutral",
        "model": "mock-model",
    }

    response = client.post(
        "/api/v1/extract",
        json={"text": "Agent development with FastAPI is useful."},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "这是一段摘要。"
    assert response.json()["keywords"] == ["Agent", "FastAPI"]
    assert response.json()["sentiment"] == "neutral"

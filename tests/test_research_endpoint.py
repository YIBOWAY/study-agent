from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routes.research.run_workflow", new_callable=AsyncMock)
def test_research_endpoint_runs_workflow(mock_run_workflow: AsyncMock) -> None:
    mock_run_workflow.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["chunking strategy rag retrieval"],
        "steps": [
            {
                "node": "rewrite_query",
                "action": "Rewrote topic to search query",
                "output_summary": "chunking strategy rag retrieval",
                "timestamp": "2026-04-19T15:30:00+00:00",
            }
        ],
        "iterations_used": 1,
        "search_result_count": 3,
    }

    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "workflow", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "workflow"
    assert response.json()["iterations_used"] == 1


@patch("app.api.routes.research.run_agent", new_callable=AsyncMock)
def test_research_endpoint_runs_agent(mock_run_agent: AsyncMock) -> None:
    mock_run_agent.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["chunking strategy rag retrieval", "semantic splitting methods"],
        "steps": [
            {
                "node": "rewrite_query",
                "action": "Rewrote topic to search query",
                "output_summary": "chunking strategy rag retrieval",
                "timestamp": "2026-04-19T15:30:00+00:00",
            }
        ],
        "iterations_used": 2,
        "search_result_count": 6,
    }

    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "agent", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "agent"
    assert response.json()["search_result_count"] == 6


@patch("app.api.routes.research.run_agent", new_callable=AsyncMock)
def test_research_endpoint_returns_generic_error(mock_run_agent: AsyncMock) -> None:
    mock_run_agent.side_effect = RuntimeError("unexpected failure")

    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "agent", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to run research workflow."


def test_research_endpoint_rejects_invalid_mode() -> None:
    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "invalid", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 422


def test_research_endpoint_rejects_empty_topic() -> None:
    response = client.post(
        "/api/v1/research",
        json={"topic": "", "mode": "workflow", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 422

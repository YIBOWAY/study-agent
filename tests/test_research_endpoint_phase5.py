from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routes.research.run_agent_v2", new_callable=AsyncMock)
def test_research_agent_v2_mode(mock_run_agent_v2: AsyncMock) -> None:
    mock_run_agent_v2.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["rag chunk overlap recall"],
        "steps": [
            {
                "node": "plan",
                "action": "Generated research plan",
                "output_summary": "2 sub-tasks",
                "timestamp": "2026-04-21T15:30:00+00:00",
            }
        ],
        "iterations_used": 1,
        "search_result_count": 2,
        "plan": ["How does overlap affect recall?"],
        "reflection_history": "pass",
        "insights_used": 1,
    }

    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "agent_v2", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "agent_v2"
    assert response.json()["plan"] == ["How does overlap affect recall?"]
    assert response.json()["insights_used"] == 1


@patch("app.api.routes.research.run_agent_v2", new_callable=AsyncMock)
def test_research_agent_v2_with_session(mock_run_agent_v2: AsyncMock) -> None:
    mock_run_agent_v2.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["rag chunk overlap recall"],
        "steps": [],
        "iterations_used": 1,
        "search_result_count": 2,
        "plan": ["How does overlap affect recall?"],
        "reflection_history": "pass",
        "insights_used": 2,
    }

    response = client.post(
        "/api/v1/research",
        json={
            "topic": "RAG chunking impact",
            "mode": "agent_v2",
            "max_iterations": 3,
            "top_k": 5,
            "session_id": "session-1",
        },
    )

    assert response.status_code == 200
    assert response.json()["insights_used"] == 2
    assert mock_run_agent_v2.await_args.kwargs["session_id"] == "session-1"


@patch("app.api.routes.research.run_multi_agent", new_callable=AsyncMock)
def test_research_multi_agent_mode(mock_run_multi_agent: AsyncMock) -> None:
    mock_run_multi_agent.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["rag chunk overlap recall"],
        "steps": [
            {
                "node": "analyst",
                "action": "Analyzed evidence",
                "output_summary": "sufficient: Evidence is coherent.",
                "timestamp": "2026-04-21T15:30:00+00:00",
            }
        ],
        "iterations_used": 1,
        "search_result_count": 2,
        "plan": ["How does overlap affect recall?"],
        "analysis": "Evidence is coherent.",
        "review_verdict": "approved",
        "agents_involved": ["planner", "researcher", "analyst", "writer", "reviewer"],
    }

    response = client.post(
        "/api/v1/research",
        json={"topic": "RAG chunking impact", "mode": "multi_agent", "max_iterations": 3, "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "multi_agent"
    assert response.json()["analysis"] == "Evidence is coherent."
    assert response.json()["review_verdict"] == "approved"
    assert response.json()["agents_involved"] == ["planner", "researcher", "analyst", "writer", "reviewer"]


@patch("app.api.routes.research.run_multi_agent", new_callable=AsyncMock)
def test_research_multi_agent_with_session(mock_run_multi_agent: AsyncMock) -> None:
    mock_run_multi_agent.return_value = {
        "report": "# Report\n\nSummary",
        "queries": ["rag chunk overlap recall"],
        "steps": [],
        "iterations_used": 1,
        "search_result_count": 2,
        "plan": ["How does overlap affect recall?"],
        "analysis": "Evidence is coherent.",
        "review_verdict": "approved",
        "agents_involved": ["planner", "researcher", "analyst", "writer", "reviewer"],
    }

    response = client.post(
        "/api/v1/research",
        json={
            "topic": "RAG chunking impact",
            "mode": "multi_agent",
            "max_iterations": 3,
            "top_k": 5,
            "session_id": "session-1",
        },
    )

    assert response.status_code == 200
    assert mock_run_multi_agent.await_args.kwargs["session_id"] == "session-1"

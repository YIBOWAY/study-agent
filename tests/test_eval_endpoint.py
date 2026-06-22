from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_rag_eval_endpoint(monkeypatch: Any) -> None:
    import app.api.routes.eval as eval_route

    monkeypatch.setattr(
        eval_route,
        "run_rag_evaluation",
        AsyncMock(return_value={"total_cases": 2, "retrieval_hit_rate": 1.0}),
    )

    response = client.post("/api/v1/eval/rag", json={"limit": 2, "with_llm_judge": False})

    assert response.status_code == 200
    assert response.json()["retrieval_hit_rate"] == 1.0


def test_post_agent_eval_endpoint(monkeypatch: Any) -> None:
    import app.api.routes.eval as eval_route

    monkeypatch.setattr(
        eval_route,
        "run_agent_evaluation",
        AsyncMock(return_value={"total": 2, "success_rate": 0.5}),
    )

    response = client.post("/api/v1/eval/agent", json={"mode": "agent_v2", "limit": 2})

    assert response.status_code == 200
    assert response.json()["success_rate"] == 0.5


def test_get_results_endpoint(monkeypatch: Any, tmp_path: Path) -> None:
    import app.api.routes.eval as eval_route

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "a.json").write_text("{}", encoding="utf-8")
    (results_dir / "b.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(eval_route, "EVAL_RESULTS_DIR", results_dir)

    response = client.get("/api/v1/eval/results")

    assert response.status_code == 200
    assert response.json()["total"] == 2

import json
from typing import Any

from fastapi.testclient import TestClient
from research_api.main import create_app
from research_core.product import build_demo_workbench_snapshot


def test_health_returns_service_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "research-workbench-api",
    }


def test_workbench_snapshot_returns_full_snapshot_record() -> None:
    client = TestClient(create_app())

    response = client.get("/api/workbench/snapshot")

    assert response.status_code == 200
    assert response.json() == build_demo_workbench_snapshot().to_record()


def test_workbench_timeline_returns_snapshot_timeline_in_order() -> None:
    client = TestClient(create_app())
    snapshot_record = build_demo_workbench_snapshot().to_record()

    response = client.get("/api/workbench/timeline")

    assert response.status_code == 200
    assert response.json() == snapshot_record["timeline"]
    assert [item["id"] for item in response.json()] == [
        item["id"] for item in snapshot_record["timeline"]
    ]


def test_openapi_tags_workbench_product_endpoints() -> None:
    client = TestClient(create_app())

    openapi = client.get("/openapi.json").json()

    assert "Workbench" in {tag["name"] for tag in openapi["tags"]}
    assert openapi["paths"]["/api/workbench/snapshot"]["get"]["tags"] == [
        "Workbench"
    ]
    assert openapi["paths"]["/api/workbench/timeline"]["get"]["tags"] == [
        "Workbench"
    ]


def test_api_responses_are_json_serializable_without_python_repr_artifacts() -> None:
    client = TestClient(create_app())

    for path in ("/health", "/api/workbench/snapshot", "/api/workbench/timeline"):
        response = client.get(path)
        payload = response.json()

        assert json.loads(json.dumps(payload, allow_nan=False)) == payload
        _assert_no_python_repr_artifacts(payload)


def _assert_no_python_repr_artifacts(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_python_repr_artifacts(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_python_repr_artifacts(item)
    elif isinstance(value, str):
        assert " object at 0x" not in value
        assert not (value.startswith("(") and value.endswith(")"))
        assert not (value.startswith("<") and value.endswith(">"))
    else:
        assert value is None or isinstance(value, bool | int | float)

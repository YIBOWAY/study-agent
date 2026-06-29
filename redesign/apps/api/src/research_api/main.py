from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from research_core.product import WorkbenchSnapshot, build_demo_workbench_snapshot

WORKBENCH_TAG = "Workbench"
SnapshotProvider = Callable[[], WorkbenchSnapshot]


def create_app(snapshot_provider: SnapshotProvider | None = None) -> FastAPI:
    provider = build_demo_workbench_snapshot if snapshot_provider is None else snapshot_provider
    snapshot = provider()
    if not isinstance(snapshot, WorkbenchSnapshot):
        raise ValueError("snapshot_provider must return a WorkbenchSnapshot")

    app = FastAPI(
        title="Research Workbench API",
        openapi_tags=[
            {
                "name": WORKBENCH_TAG,
                "description": "Read-only research workbench product snapshot endpoints.",
            }
        ],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "research-workbench-api"}

    @app.get("/api/workbench/snapshot", tags=[WORKBENCH_TAG])
    def workbench_snapshot() -> dict[str, Any]:
        return snapshot.to_record()

    @app.get("/api/workbench/timeline", tags=[WORKBENCH_TAG])
    def workbench_timeline() -> list[dict[str, Any]]:
        snapshot_record = snapshot.to_record()
        return snapshot_record["timeline"]

    return app


app = create_app()

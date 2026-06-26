from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from research_core.product import build_demo_workbench_snapshot

WORKBENCH_TAG = "Workbench"


def create_app() -> FastAPI:
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
        return build_demo_workbench_snapshot().to_record()

    @app.get("/api/workbench/timeline", tags=[WORKBENCH_TAG])
    def workbench_timeline() -> list[dict[str, Any]]:
        snapshot = build_demo_workbench_snapshot().to_record()
        return snapshot["timeline"]

    return app


app = create_app()

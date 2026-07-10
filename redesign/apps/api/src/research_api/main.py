from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from research_core.product import WorkbenchSnapshot, build_demo_workbench_snapshot

WORKBENCH_TAG = "Workbench"
SnapshotProvider = Callable[[], WorkbenchSnapshot]


def create_app(snapshot_provider: SnapshotProvider | None = None) -> FastAPI:
    """Create the read-only Workbench API.

    The snapshot is resolved once at app creation. That keeps the Phase 5 demo
    deterministic and matches the product contract that ``apps/api`` is a thin
    transport over a fixed ``WorkbenchSnapshot``. Callers that need live data
    must supply a provider that already closes over current state, then rebuild
    the app (or later replace this with a request-scoped provider).
    """
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
    app.state.snapshot = snapshot
    app.state.snapshot_provider = provider

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

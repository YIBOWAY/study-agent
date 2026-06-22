from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_tracing_service
from app.services.tracing_service import TracingService

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("/traces")
async def list_traces(
    limit: int = Query(default=50, ge=1, le=500),
    name: str | None = None,
    tracing: TracingService | None = Depends(get_tracing_service),
) -> dict[str, Any]:
    if tracing is None:
        return {"traces": [], "total": 0}
    traces = await tracing.query_traces(limit=limit, name=name)
    return {"traces": traces, "total": len(traces)}


@router.get("/cost")
async def get_cost_summary(
    since: str | None = None,
    tracing: TracingService | None = Depends(get_tracing_service),
) -> dict[str, Any]:
    if tracing is None:
        return {
            "total_cost_usd": 0.0,
            "total_calls": 0,
            "total_tokens": {"prompt": 0, "completion": 0},
            "by_model": {},
            "since": since or "",
        }
    return await tracing.get_cost_summary(since=since)


@router.get("/agent_runs")
async def list_agent_runs(
    limit: int = Query(default=20, ge=1, le=200),
    tracing: TracingService | None = Depends(get_tracing_service),
) -> dict[str, Any]:
    if tracing is None:
        return {"runs": [], "total": 0}
    runs = await tracing.query_agent_runs(limit=limit)
    return {"runs": runs, "total": len(runs)}

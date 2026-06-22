from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_api_key
from app.services.memory_service import MemoryService

router = APIRouter(
    prefix="/api/v1/memory",
    tags=["memory"],
    dependencies=[Depends(require_api_key)],
)
memory_service = MemoryService()
logger = logging.getLogger(__name__)


@router.get("/insights")
async def list_insights() -> dict[str, object]:
    try:
        insights = await memory_service.get_all_insights()
        return {"insights": insights, "total": len(insights)}
    except Exception as exc:
        logger.exception("Unexpected error while listing memory insights")
        raise HTTPException(status_code=500, detail="Failed to list memory insights.") from exc


@router.get("/insights/search")
async def search_insights(query: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        insights = await memory_service.retrieve_relevant_insights(query, top_k=3)
        return {"insights": insights, "query": query}
    except Exception as exc:
        logger.exception("Unexpected error while searching memory insights")
        raise HTTPException(status_code=500, detail="Failed to search memory insights.") from exc


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, object]:
    try:
        session = await memory_service.get_session_context(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        return session
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while reading memory session")
        raise HTTPException(status_code=500, detail="Failed to read memory session.") from exc


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str) -> dict[str, str]:
    try:
        await memory_service.clear_session(session_id)
        return {"status": "cleared"}
    except Exception as exc:
        logger.exception("Unexpected error while clearing memory session")
        raise HTTPException(status_code=500, detail="Failed to clear memory session.") from exc


@router.delete("/insights")
async def clear_insights() -> dict[str, object]:
    try:
        deleted_count = await memory_service.clear_all_insights()
        return {"status": "cleared", "deleted_count": deleted_count}
    except Exception as exc:
        logger.exception("Unexpected error while clearing memory insights")
        raise HTTPException(status_code=500, detail="Failed to clear memory insights.") from exc

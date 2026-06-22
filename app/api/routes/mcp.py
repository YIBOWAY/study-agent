from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_guardrails_service
from app.services.mcp.runtime import get_mcp_runtime

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])
logger = logging.getLogger(__name__)


class MCPToolInvokeRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


@router.get("/servers")
async def list_servers() -> dict[str, object]:
    try:
        return {"servers": get_mcp_runtime().list_servers()}
    except Exception as exc:
        logger.exception("Unexpected error while listing MCP servers")
        raise HTTPException(status_code=500, detail="Failed to list MCP servers.") from exc


@router.get("/tools")
async def list_tools() -> dict[str, object]:
    try:
        tools = get_mcp_runtime().list_all_tools()
        return {"tools": tools, "total": len(tools)}
    except Exception as exc:
        logger.exception("Unexpected error while listing MCP tools")
        raise HTTPException(status_code=500, detail="Failed to list MCP tools.") from exc


@router.post("/tools/{tool_name}/invoke")
async def invoke_tool(
    tool_name: str,
    request: MCPToolInvokeRequest,
    guardrails=Depends(get_guardrails_service),
) -> dict[str, object]:
    # Local/debug-only endpoint. Do not expose this route publicly without auth.
    if guardrails is not None:
        validation = guardrails.validate_tool_call(tool_name, request.arguments)
        if not validation["safe"]:
            raise HTTPException(status_code=400, detail=validation["reason"])

    try:
        return await get_mcp_runtime().execute_tool(tool_name, request.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while invoking MCP tool")
        raise HTTPException(status_code=500, detail="Failed to invoke MCP tool.") from exc

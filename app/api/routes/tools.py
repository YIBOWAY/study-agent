import logging

from fastapi import APIRouter, HTTPException

from app.schemas.tools import ToolChatRequest, ToolChatResponse, ToolListResponse
from app.services.llm_service import LLMService
from app.services.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])
llm_service = LLMService()
tool_registry = ToolRegistry()
logger = logging.getLogger(__name__)


@router.get("/list", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    return ToolListResponse(tools=tool_registry.get_tool_infos())


@router.post("/chat", response_model=ToolChatResponse)
async def chat_with_tools(request: ToolChatRequest) -> ToolChatResponse:
    try:
        tools = tool_registry.get_openai_tools_schema(request.enabled_tools)
        max_iterations = request.max_iterations or tool_registry.settings.tool_call_max_iterations
        result = await llm_service.chat_with_tools(
            user_message=request.message,
            tools=tools,
            tool_executor=tool_registry,
            max_iterations=max_iterations,
            system_prompt=request.system_prompt,
        )
        return ToolChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while handling tool chat")
        raise HTTPException(status_code=500, detail="Failed to complete tool chat.") from exc

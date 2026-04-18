from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse, ExtractRequest, ExtractResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1", tags=["llm"])
llm_service = LLMService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = await llm_service.chat(
            user_message=request.message,
            system_prompt=request.system_prompt,
        )
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest) -> ExtractResponse:
    try:
        result = await llm_service.extract(request.text)
        return ExtractResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

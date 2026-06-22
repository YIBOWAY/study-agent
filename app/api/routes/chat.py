import json

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_guardrails_service, get_tracing_service
from app.schemas.chat import ChatRequest, ChatResponse, ExtractRequest, ExtractResponse
from app.services.guardrails_service import GuardrailsService
from app.services.llm_service import LLMService
from app.services.tracing_service import TracingService

router = APIRouter(prefix="/api/v1", tags=["chat"])
llm_service = LLMService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest = Body(
        ...,
        openapi_examples={
            "basic_chat": {
                "summary": "Basic chat request",
                "value": {
                    "message": "Summarize what this research platform can do in one paragraph.",
                    "system_prompt": None,
                },
            }
        },
    ),
    guardrails: GuardrailsService | None = Depends(get_guardrails_service),
    tracing: TracingService | None = Depends(get_tracing_service),
) -> ChatResponse:
    try:
        result = await llm_service.chat(
            user_message=request.message,
            system_prompt=request.system_prompt,
            guardrails=guardrails,
            tracing=tracing,
        )
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest = Body(
        ...,
        openapi_examples={
            "streaming_chat": {
                "summary": "Streaming chat request",
                "value": {
                    "message": "Explain the difference between agent_v2 and multi_agent.",
                    "system_prompt": None,
                },
            }
        },
    ),
    guardrails: GuardrailsService | None = Depends(get_guardrails_service),
) -> StreamingResponse:
    if guardrails is not None:
        input_check = guardrails.check_input(request.message)
        if not input_check["safe"]:
            raise HTTPException(status_code=400, detail=str(input_check["sanitized_input"]))
        message = str(input_check["sanitized_input"])
    else:
        message = request.message

    async def event_stream():
        async for chunk in llm_service.chat_stream(
            user_message=message,
            system_prompt=request.system_prompt,
        ):
            if guardrails is not None:
                chunk = str(guardrails.sanitize_output(chunk)["sanitized"])
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest = Body(
        ...,
        openapi_examples={
            "extract": {
                "summary": "Extract structured info",
                "value": {
                    "text": "The team shipped a new evaluation pipeline and tracked the rollout in a local trace database.",
                },
            }
        },
    )
) -> ExtractResponse:
    try:
        result = await llm_service.extract(request.text)
        return ExtractResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

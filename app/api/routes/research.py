import logging
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_guardrails_service, get_tracing_service
from app.api.routes.memory import memory_service
from app.core.auth import require_api_key
from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.guardrails_service import GuardrailsService
from app.services.llm_service import LLMService
from app.services.multi_agent import run_multi_agent
from app.services.rag_service import RAGService
from app.services.research import run_agent, run_agent_v2, run_workflow
from app.services.research.streaming import stream_research_events
from app.services.tool_registry import ToolRegistry
from app.services.tracing_service import TracingService

router = APIRouter(
    prefix="/api/v1/research",
    tags=["research"],
    dependencies=[Depends(require_api_key)],
)
llm_service = LLMService()
rag_service = RAGService(llm_service=llm_service)
tool_registry = ToolRegistry(rag_service=rag_service)
logger = logging.getLogger(__name__)


@router.post("", response_model=ResearchResponse)
async def research(
    request: ResearchRequest = Body(
        ...,
        openapi_examples={
            "agent_v2": {
                "summary": "Enhanced single-agent research run",
                "value": {
                    "topic": "What changed in Phase 8 of this project?",
                    "mode": "agent_v2",
                    "max_iterations": 3,
                    "top_k": 5,
                    "session_id": "demo-session",
                },
            },
            "multi_agent": {
                "summary": "Multi-agent research run",
                "value": {
                    "topic": "Compare workflow, agent_v2, and multi_agent modes.",
                    "mode": "multi_agent",
                    "max_iterations": 3,
                    "top_k": 5,
                    "session_id": "demo-session",
                },
            },
        },
    ),
    stream: bool = Query(default=False),
    guardrails: GuardrailsService | None = Depends(get_guardrails_service),
    tracing: TracingService | None = Depends(get_tracing_service),
) -> ResearchResponse | StreamingResponse:
    topic = request.topic
    if guardrails is not None:
        input_check = guardrails.check_input(request.topic)
        if not input_check["safe"]:
            raise HTTPException(status_code=400, detail=str(input_check["sanitized_input"]))
        topic = str(input_check["sanitized_input"])

    llm_service.attach_tracing_service(tracing)
    tool_registry.attach_tracing_service(tracing)

    if stream:
        return StreamingResponse(
            _research_event_stream(request, topic, tracing),
            media_type="text/event-stream",
        )

    try:
        if tracing is None:
            result = await _run_research_mode(request, topic)
        else:
            async with tracing.trace(
                "agent_run",
                {"mode": request.mode, "topic": topic},
            ):
                result = await _run_research_mode(request, topic)
        return ResearchResponse(topic=topic, mode=request.mode, **result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while running research workflow")
        raise HTTPException(status_code=500, detail="Failed to run research workflow.") from exc


async def _research_event_stream(
    request: ResearchRequest,
    topic: str,
    tracing: TracingService | None,
) -> AsyncIterator[str]:
    if tracing is None:
        async for event in _stream_research_events(request, topic):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    else:
        async with tracing.trace(
            "agent_run",
            {"mode": request.mode, "topic": topic, "stream": True},
        ):
            async for event in _stream_research_events(request, topic):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_research_events(
    request: ResearchRequest,
    topic: str,
) -> AsyncIterator[dict[str, object]]:
    async for event in stream_research_events(
        request.mode,
        topic=topic,
        max_iterations=request.max_iterations,
        top_k=request.top_k,
        rag_service=rag_service,
        llm_service=llm_service,
        tool_registry=tool_registry,
        memory_service=memory_service,
        session_id=request.session_id,
    ):
        yield event


async def _run_research_mode(request: ResearchRequest, topic: str) -> dict[str, object]:
    if request.mode == "workflow":
        return await run_workflow(
            topic=topic,
            max_iterations=request.max_iterations,
            top_k=request.top_k,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
        )
    if request.mode == "agent":
        return await run_agent(
            topic=topic,
            max_iterations=request.max_iterations,
            top_k=request.top_k,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
        )
    if request.mode == "agent_v2":
        return await run_agent_v2(
            topic=topic,
            max_iterations=request.max_iterations,
            top_k=request.top_k,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
            memory_service=memory_service,
            session_id=request.session_id,
        )
    return await run_multi_agent(
        topic=topic,
        max_iterations=request.max_iterations,
        top_k=request.top_k,
        rag_service=rag_service,
        llm_service=llm_service,
        tool_registry=tool_registry,
        memory_service=memory_service,
        session_id=request.session_id,
    )

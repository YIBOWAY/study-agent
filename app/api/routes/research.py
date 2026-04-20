import logging

from fastapi import APIRouter, HTTPException

from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.research import run_agent, run_workflow
from app.services.tool_registry import ToolRegistry

router = APIRouter(prefix="/api/v1/research", tags=["research"])
llm_service = LLMService()
rag_service = RAGService(llm_service=llm_service)
tool_registry = ToolRegistry(rag_service=rag_service)
logger = logging.getLogger(__name__)


@router.post("", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    try:
        if request.mode == "workflow":
            result = await run_workflow(
                topic=request.topic,
                max_iterations=request.max_iterations,
                top_k=request.top_k,
                rag_service=rag_service,
                llm_service=llm_service,
                tool_registry=tool_registry,
            )
        else:
            result = await run_agent(
                topic=request.topic,
                max_iterations=request.max_iterations,
                top_k=request.top_k,
                rag_service=rag_service,
                llm_service=llm_service,
                tool_registry=tool_registry,
            )
        return ResearchResponse(topic=request.topic, mode=request.mode, **result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while running research workflow")
        raise HTTPException(status_code=500, detail="Failed to run research workflow.") from exc

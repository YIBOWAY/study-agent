from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from scripts.run_agent_eval import run_agent_evaluation
from scripts.run_rag_eval import RESULTS_DIR as EVAL_RESULTS_DIR
from scripts.run_rag_eval import run_rag_evaluation

router = APIRouter(prefix="/api/v1/eval", tags=["eval"])


class RAGEvalRequest(BaseModel):
    limit: int = Field(default=10, ge=1)
    with_llm_judge: bool = False


class AgentEvalRequest(BaseModel):
    mode: Literal["workflow", "agent", "agent_v2", "multi_agent"] = "agent_v2"
    limit: int = Field(default=5, ge=1)


@router.post("/rag")
async def evaluate_rag(request: RAGEvalRequest) -> dict[str, Any]:
    try:
        return await run_rag_evaluation(
            cases_path="eval/rag_questions.jsonl",
            limit=request.limit,
            with_llm_judge=request.with_llm_judge,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to run RAG evaluation.") from exc


@router.post("/agent")
async def evaluate_agent(request: AgentEvalRequest) -> dict[str, Any]:
    try:
        return await run_agent_evaluation(
            mode=request.mode,
            limit=request.limit,
            cases_path="eval/agent_topics.jsonl",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to run agent evaluation.") from exc


@router.get("/results")
async def list_eval_results() -> dict[str, Any]:
    files = sorted(Path(EVAL_RESULTS_DIR).glob("*.json"))
    return {
        "results": [
            {"name": file.name, "path": str(file), "size": file.stat().st_size}
            for file in files
        ],
        "total": len(files),
    }

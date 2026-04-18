import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.rag import AskRequest, AskResponse, IngestResponse, SearchRequest, SearchResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
rag_service = RAGService()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    supported_types = {
        "application/pdf",
        "text/markdown",
        "text/plain",
        "application/octet-stream",
    }
    filename = file.filename or "uploaded"
    is_markdown = filename.lower().endswith(".md")

    if file.content_type not in supported_types and not is_markdown:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and Markdown files are supported.",
        )

    try:
        file_bytes = await file.read()
        if file.content_type == "application/pdf" and not is_markdown:
            result = await rag_service.ingest_pdf(file_bytes, filename)
        else:
            text = file_bytes.decode("utf-8")
            result = await rag_service.ingest_text(text, filename)
        return IngestResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while ingesting file")
        raise HTTPException(status_code=500, detail="Failed to ingest file.") from exc


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    try:
        result = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )
        return SearchResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while searching RAG index")
        raise HTTPException(status_code=500, detail="Failed to search RAG index.") from exc


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    try:
        result = await rag_service.ask(
            query=request.query,
            top_k=request.top_k,
            final_k=request.final_k,
            document_id=request.document_id,
        )
        return AskResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while generating RAG answer")
        raise HTTPException(status_code=500, detail="Failed to generate RAG answer.") from exc

import logging

from fastapi import APIRouter, Body, File, HTTPException, UploadFile

from app.schemas.rag import AskRequest, AskResponse, IngestResponse, SearchRequest, SearchResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
rag_service = RAGService()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)) -> IngestResponse:
    filename = file.filename or "uploaded"
    lowercase_filename = filename.lower()
    is_markdown = lowercase_filename.endswith(".md")

    try:
        file_bytes = await file.read()
        is_octet_stream_pdf = (
            file.content_type == "application/octet-stream"
            and (lowercase_filename.endswith(".pdf") or file_bytes.startswith(b"%PDF-"))
        )
        is_pdf = not is_markdown and (
            file.content_type == "application/pdf" or is_octet_stream_pdf
        )
        is_text = is_markdown or file.content_type in {"text/markdown", "text/plain"}

        if not is_pdf and not is_text:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, Markdown, and plain text files are supported.",
            )

        if is_pdf:
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
async def search(
    request: SearchRequest = Body(
        ...,
        openapi_examples={
            "search": {
                "summary": "Search indexed chunks",
                "value": {
                    "query": "What changed in Phase 8?",
                    "top_k": 5,
                    "document_id": None,
                },
            }
        },
    )
) -> SearchResponse:
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
async def ask(
    request: AskRequest = Body(
        ...,
        openapi_examples={
            "ask": {
                "summary": "Ask a grounded question over indexed files",
                "value": {
                    "query": "How does the platform expose streaming chat?",
                    "top_k": 5,
                    "final_k": 3,
                    "document_id": None,
                },
            }
        },
    )
) -> AskResponse:
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

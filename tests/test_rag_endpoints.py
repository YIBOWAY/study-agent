from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routes.rag.rag_service.ingest_pdf", new_callable=AsyncMock)
def test_ingest_endpoint_accepts_pdf(mock_ingest: AsyncMock) -> None:
    mock_ingest.return_value = {
        "document_id": "doc-1",
        "filename": "guide.pdf",
        "chunk_count": 3,
    }

    response = client.post(
        "/api/v1/rag/ingest",
        files={"file": ("guide.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["chunk_count"] == 3


@patch("app.api.routes.rag.rag_service.search", new_callable=AsyncMock)
def test_search_endpoint_returns_results(mock_search: AsyncMock) -> None:
    mock_search.return_value = {
        "results": [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "source_name": "guide.pdf",
                "text": "Revenue grew 20% year over year.",
                "page_number": 2,
                "score": 0.91,
            }
        ],
        "embedding_model": "text-embedding-3-large",
        "rerank_model": "rerank-v3.5",
    }

    response = client.post(
        "/api/v1/rag/search",
        json={"query": "How did revenue change?", "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["chunk_id"] == "chunk-1"
    assert response.json()["embedding_model"] == "text-embedding-3-large"
    assert "model" not in response.json()


@patch("app.api.routes.rag.rag_service.search", new_callable=AsyncMock)
def test_search_endpoint_returns_generic_error_for_unexpected_exception(mock_search: AsyncMock) -> None:
    mock_search.side_effect = RuntimeError("sensitive backend failure")

    response = client.post(
        "/api/v1/rag/search",
        json={"query": "How did revenue change?", "top_k": 5},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search RAG index."


@patch("app.api.routes.rag.rag_service.ask", new_callable=AsyncMock)
def test_ask_endpoint_returns_answer_and_sources(mock_ask: AsyncMock) -> None:
    mock_ask.return_value = {
        "answer": "Revenue grew 20% year over year.",
        "sources": [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "source_name": "guide.pdf",
                "text": "Revenue grew 20% year over year.",
                "page_number": 2,
                "score": 0.97,
            }
        ],
        "context": "internal context should not be exposed",
        "model": "gpt-5.4",
        "rerank_model": "rerank-v3.5",
    }

    response = client.post(
        "/api/v1/rag/ask",
        json={"query": "How did revenue change?", "top_k": 10, "final_k": 3},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Revenue grew 20% year over year."
    assert response.json()["sources"][0]["page_number"] == 2
    assert response.json()["model"] == "gpt-5.4"
    assert response.json()["rerank_model"] == "rerank-v3.5"
    assert "context" not in response.json()


def test_ask_endpoint_rejects_final_k_greater_than_top_k() -> None:
    response = client.post(
        "/api/v1/rag/ask",
        json={"query": "How did revenue change?", "top_k": 1, "final_k": 3},
    )

    assert response.status_code == 422

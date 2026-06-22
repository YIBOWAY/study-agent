from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.schemas.rag import SearchResult
from app.services.rerank_service import RerankService


class DummyResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FailingHTTPResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.request = httpx.Request("POST", "https://api.cohere.com/v2/rerank")
        self.response = httpx.Response(status_code=status_code, request=self.request)

    def raise_for_status(self) -> None:
        raise httpx.HTTPStatusError(
            f"Client error '{self.status_code}'",
            request=self.request,
            response=self.response,
        )


@pytest.fixture
def rerank_settings() -> Settings:
    return Settings(
        _env_file=None,
        llm_api_key="llm-key",
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
        rerank_fail_soft=True,
    )


@pytest.fixture
def rerank_candidates() -> list[SearchResult]:
    return [
        SearchResult(
            chunk_id="chunk-a",
            document_id="doc-1",
            source_name="guide.pdf",
            text="Revenue was flat.",
            page_number=1,
            score=0.2,
        ),
        SearchResult(
            chunk_id="chunk-b",
            document_id="doc-1",
            source_name="guide.pdf",
            text="Revenue grew 20% year over year.",
            page_number=2,
            score=0.3,
        ),
    ]


@patch("app.services.rerank_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_rerank_reorders_candidates(
    mock_client: AsyncMock,
    rerank_settings: Settings,
    rerank_candidates: list[SearchResult],
) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(
        {
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.41},
            ]
        }
    )
    mock_client.return_value.__aenter__.return_value = client_instance

    service = RerankService(settings=rerank_settings)

    reranked = await service.rerank("How did revenue change?", rerank_candidates, final_k=2)

    assert [item.chunk_id for item in reranked] == ["chunk-b", "chunk-a"]
    assert reranked[0].score == 0.95
    mock_client.assert_called_once_with(timeout=rerank_settings.llm_timeout, follow_redirects=True)
    client_instance.post.assert_awaited_once_with(
        "https://api.cohere.com/v2/rerank",
        headers={
            "Authorization": "Bearer rerank-key",
            "Content-Type": "application/json",
        },
        json={
            "model": rerank_settings.rerank_model,
            "query": "How did revenue change?",
            "documents": [candidate.text for candidate in rerank_candidates],
            "top_n": 2,
        },
    )


@pytest.mark.asyncio
async def test_rerank_empty_candidates_returns_empty_list(rerank_settings: Settings) -> None:
    service = RerankService(settings=rerank_settings)

    reranked = await service.rerank("query", [], final_k=3)

    assert reranked == []


@pytest.mark.asyncio
async def test_rerank_missing_api_key_raises_value_error() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        qdrant_url="http://localhost:6333",
        rerank_api_key="",
    )
    service = RerankService(settings=settings)
    candidates = [
        SearchResult(
            chunk_id="chunk-a",
            document_id="doc-1",
            source_name="guide.pdf",
            text="Revenue was flat.",
            page_number=1,
            score=0.2,
        )
    ]

    with pytest.raises(ValueError, match="RERANK_API_KEY"):
        await service.rerank("query", candidates, final_k=1)


@patch("app.services.rerank_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_rerank_invalid_returned_index_raises_value_error(
    mock_client: AsyncMock,
    rerank_settings: Settings,
    rerank_candidates: list[SearchResult],
) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(
        {
            "results": [
                {"index": 5, "relevance_score": 0.95},
            ]
        }
    )
    mock_client.return_value.__aenter__.return_value = client_instance

    service = RerankService(settings=rerank_settings)

    with pytest.raises(ValueError, match="index"):
        await service.rerank("query", rerank_candidates, final_k=1)


@pytest.mark.parametrize(
    ("payload", "error_match"),
    [
        ({}, "'results' must be a list"),
        ({"results": "bad"}, "'results' must be a list"),
        ({"results": [{}]}, "missing 'index'"),
        (
            {"results": [{"index": 0, "relevance_score": "bad"}]},
            "invalid relevance_score",
        ),
    ],
)
@patch("app.services.rerank_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_rerank_malformed_provider_payload_raises_value_error(
    mock_client: AsyncMock,
    payload: dict[str, object],
    error_match: str,
    rerank_settings: Settings,
    rerank_candidates: list[SearchResult],
) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(payload)
    mock_client.return_value.__aenter__.return_value = client_instance

    service = RerankService(settings=rerank_settings)

    with pytest.raises(ValueError, match=error_match):
        await service.rerank("query", rerank_candidates, final_k=2)


@patch("app.services.rerank_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_rerank_provider_403_falls_back_when_fail_soft_enabled(
    mock_client: AsyncMock,
    rerank_settings: Settings,
    rerank_candidates: list[SearchResult],
) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = FailingHTTPResponse(403)
    mock_client.return_value.__aenter__.return_value = client_instance

    service = RerankService(settings=rerank_settings)

    reranked = await service.rerank("query", rerank_candidates, final_k=1)

    assert [item.chunk_id for item in reranked] == ["chunk-a"]


@patch("app.services.rerank_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_rerank_provider_403_raises_when_fail_soft_disabled(
    mock_client: AsyncMock,
    rerank_candidates: list[SearchResult],
) -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
        rerank_fail_soft=False,
    )
    client_instance = AsyncMock()
    client_instance.post.return_value = FailingHTTPResponse(403)
    mock_client.return_value.__aenter__.return_value = client_instance

    service = RerankService(settings=settings)

    with pytest.raises(httpx.HTTPStatusError):
        await service.rerank("query", rerank_candidates, final_k=1)

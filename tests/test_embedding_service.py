from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.embedding_service import EmbeddingService


class DummyResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


@patch("app.services.embedding_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_embed_texts_calls_embeddings_endpoint(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(
        {"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]}
    )
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        embedding_base_url="https://api.xairouter.com/v1",
        embedding_model="text-embedding-3-large",
        embedding_dimensions=2,
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    result = await service.embed_texts(["alpha", "beta"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    mock_client.assert_called_once_with(timeout=settings.embedding_timeout, follow_redirects=True, trust_env=True)
    client_instance.post.assert_awaited_once_with(
        "https://api.xairouter.com/v1/embeddings",
        headers={
            "Authorization": "Bearer llm-key",
            "Content-Type": "application/json",
        },
        json={
            "input": ["alpha", "beta"],
            "model": "text-embedding-3-large",
        },
    )


@pytest.mark.asyncio
async def test_embed_texts_missing_api_key_raises_value_error() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="",
        embedding_api_key="",
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match="EMBEDDING_API_KEY"):
        await service.embed_texts(["alpha"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, error_match",
    [
        ({}, "data"),
        ({"data": "not-a-list"}, "data"),
        ({"data": [{}]}, "embedding"),
        ({"data": [{"embedding": "not-a-list"}]}, "embedding"),
    ],
)
@patch("app.services.embedding_service.httpx.AsyncClient")
async def test_embed_texts_malformed_payload_raises_value_error(
    mock_client: AsyncMock,
    payload: dict[str, object],
    error_match: str,
) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(payload)
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        embedding_base_url="https://api.xairouter.com/v1",
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match=error_match):
        await service.embed_texts(["alpha"])
@patch("app.services.embedding_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_embed_texts_rejects_cardinality_mismatch(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"data": [{"embedding": [0.1, 0.2]}]})
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        embedding_base_url="https://api.xairouter.com/v1",
        embedding_dimensions=2,
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match="2 inputs"):
        await service.embed_texts(["alpha", "beta"])


    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"data": [{"embedding": [0.1, 0.2]}]})
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        embedding_base_url="https://api.xairouter.com/v1",
        embedding_dimensions=3,
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match="dimension"):
        await service.embed_texts(["alpha"])


@patch("app.services.embedding_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_embed_query_propagates_dimension_mismatch(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"data": [{"embedding": [0.1, 0.2]}]})
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        embedding_dimensions=3,
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match="dimension"):
        await service.embed_query("alpha")

@patch("app.services.embedding_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_embed_query_empty_response_raises_value_error(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse({"data": []})
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        qdrant_url="http://localhost:6333",
        rerank_api_key="rerank-key",
    )
    service = EmbeddingService(settings=settings)

    with pytest.raises(ValueError, match="empty"):
        await service.embed_query("alpha")

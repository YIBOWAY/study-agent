import pytest
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app.core.config import Settings
from app.schemas.rag import ChunkRecord
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService


class FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeCollectionsResponse:
    def __init__(self, names: list[str]) -> None:
        self.collections = [FakeCollection(name) for name in names]


class FakeScoredPoint:
    def __init__(self, id: str, score: float, payload: dict[str, object] | None) -> None:
        self.id = id
        self.score = score
        self.payload = payload


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collection_names: list[str] = []
        self.created_collections: list[dict[str, object]] = []
        self.upserted_points: list[object] = []
        self.search_calls: list[dict[str, object]] = []
        self.search_results: list[FakeScoredPoint] = []

    async def get_collections(self) -> FakeCollectionsResponse:
        return FakeCollectionsResponse(self.collection_names)

    async def create_collection(self, collection_name: str, vectors_config: object) -> None:
        self.collection_names.append(collection_name)
        self.created_collections.append(
            {"collection_name": collection_name, "vectors_config": vectors_config}
        )

    async def upsert(self, collection_name: str, points: list[object]) -> None:
        self.upserted_points.extend(points)

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        query_filter: object | None = None,
    ) -> list[FakeScoredPoint]:
        self.search_calls.append(
            {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "limit": limit,
                "query_filter": query_filter,
            }
        )
        return self.search_results[:limit]


class FakeEmbeddingService:
    async def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        llm_api_key="llm-key",
        qdrant_url="http://localhost:6333",
        qdrant_collection="test_chunks",
        embedding_dimensions=3,
        rerank_api_key="rerank-key",
    )


@pytest.mark.asyncio
async def test_vector_store_upserts_chunk_payloads() -> None:
    client = FakeQdrantClient()
    service = VectorStoreService(settings=make_settings(), client=client)
    chunks = [
        ChunkRecord(
            chunk_id="chunk-1",
            document_id="doc-1",
            source_name="guide.pdf",
            text="Revenue grew year over year.",
            page_number=7,
            section_title="Financials",
        )
    ]

    await service.upsert_chunks(chunks, [[0.1, 0.2, 0.3]])

    assert len(client.created_collections) == 1
    assert len(client.upserted_points) == 1
    point = client.upserted_points[0]
    assert point.id == "chunk-1"
    assert point.vector == [0.1, 0.2, 0.3]
    assert point.payload == {
        "document_id": "doc-1",
        "source_name": "guide.pdf",
        "text": "Revenue grew year over year.",
        "page_number": 7,
        "section_title": "Financials",
    }


@pytest.mark.asyncio
async def test_vector_store_does_not_recreate_existing_collection() -> None:
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    service = VectorStoreService(settings=make_settings(), client=client)

    await service.ensure_collection()

    assert client.collection_names == ["test_chunks"]
    assert client.created_collections == []


@pytest.mark.asyncio
async def test_vector_store_rejects_mismatched_chunks_and_vectors() -> None:
    client = FakeQdrantClient()
    service = VectorStoreService(settings=make_settings(), client=client)
    chunks = [
        ChunkRecord(
            chunk_id="chunk-1",
            document_id="doc-1",
            source_name="guide.pdf",
            text="Revenue grew year over year.",
        )
    ]

    with pytest.raises(ValueError, match="zip.*argument"):
        await service.upsert_chunks(chunks, [])

    assert client.upserted_points == []


@pytest.mark.asyncio
async def test_retrieval_service_returns_vector_matches() -> None:
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    client.search_results = [
        FakeScoredPoint(
            id="chunk-1",
            score=0.92,
            payload={
                "document_id": "doc-1",
                "source_name": "guide.pdf",
                "text": "Revenue grew year over year.",
                "page_number": 7,
                "section_title": "Financials",
            },
        )
    ]
    vector_store = VectorStoreService(settings=make_settings(), client=client)
    service = RetrievalService(
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
    )

    results = await service.retrieve("revenue growth", top_k=3, document_id="doc-1")

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].document_id == "doc-1"
    assert results[0].source_name == "guide.pdf"
    assert results[0].text == "Revenue grew year over year."
    assert results[0].page_number == 7
    assert results[0].score == 0.92
    assert client.search_calls[0]["query_vector"] == [0.1, 0.2, 0.3]
    assert client.search_calls[0]["limit"] == 3
    query_filter = client.search_calls[0]["query_filter"]
    assert isinstance(query_filter, Filter)


@pytest.mark.asyncio
async def test_vector_store_rejects_invalid_required_field_types() -> None:
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    client.search_results = [
        FakeScoredPoint(
            id="chunk-1",
            score=0.92,
            payload={
                "document_id": 123,
                "source_name": "guide.pdf",
                "text": "Revenue grew year over year.",
            },
        )
    ]
    service = VectorStoreService(settings=make_settings(), client=client)

    with pytest.raises(ValueError, match="document_id"):
        await service.search(query_vector=[0.1, 0.2, 0.3], top_k=3)


@pytest.mark.asyncio
async def test_vector_store_rejects_invalid_score() -> None:
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    client.search_results = [
        FakeScoredPoint(
            id="chunk-1",
            score="bad-score",
            payload={
                "document_id": "doc-1",
                "source_name": "guide.pdf",
                "text": "Revenue grew year over year.",
            },
        )
    ]
    service = VectorStoreService(settings=make_settings(), client=client)

    with pytest.raises(ValueError, match="score"):
        await service.search(query_vector=[0.1, 0.2, 0.3], top_k=3)
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    client.search_results = [
        FakeScoredPoint(
            id="chunk-1",
            score=0.92,
            payload={
                "source_name": "guide.pdf",
                "text": "Revenue grew year over year.",
            },
        )
    ]
    service = VectorStoreService(settings=make_settings(), client=client)

    with pytest.raises(ValueError, match="document_id"):
        await service.search(query_vector=[0.1, 0.2, 0.3], top_k=3)


@pytest.mark.asyncio
async def test_vector_store_rejects_non_mapping_payload() -> None:
    client = FakeQdrantClient()
    client.collection_names.append("test_chunks")
    client.search_results = [
        FakeScoredPoint(
            id="chunk-1",
            score=0.92,
            payload=None,
        )
    ]
    service = VectorStoreService(settings=make_settings(), client=client)

    with pytest.raises(ValueError, match="payload"):
        await service.search(query_vector=[0.1, 0.2, 0.3], top_k=3)

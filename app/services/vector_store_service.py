from __future__ import annotations

from typing import Mapping, Sequence

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import Settings, get_settings
from app.schemas.rag import ChunkRecord, SearchResult


class VectorStoreService:
    def __init__(
        self,
        settings: Settings | None = None,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key or None,
        )

    async def ensure_collection(self) -> None:
        response = await self.client.get_collections()
        collection_names = {collection.name for collection in response.collections}
        if self.settings.qdrant_collection in collection_names:
            return

        await self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=VectorParams(
                size=self.settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )

    async def upsert_chunks(
        self,
        chunks: Sequence[ChunkRecord],
        vectors: Sequence[list[float]],
    ) -> None:
        await self.ensure_collection()
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "document_id": chunk.document_id,
                    "source_name": chunk.source_name,
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        await self.client.upsert(
            collection_name=self.settings.qdrant_collection,
            points=points,
        )

    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        query_filter = None
        if document_id is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )

        points = await self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        return [
            self._build_search_result(point)
            for point in points
        ]

    @staticmethod
    def _build_search_result(point: object) -> SearchResult:
        point_id = getattr(point, "id", None)
        payload = getattr(point, "payload", None)
        if not isinstance(payload, Mapping):
            raise ValueError(f"Qdrant point {point_id} has invalid payload; expected mapping.")

        required_fields = ("document_id", "source_name", "text")
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Qdrant point {point_id} payload is missing required field(s): {missing}.")

        document_id = payload["document_id"]
        source_name = payload["source_name"]
        text = payload["text"]
        if not isinstance(document_id, str):
            raise ValueError(f"Qdrant point {point_id} payload field 'document_id' must be a string.")
        if not isinstance(source_name, str):
            raise ValueError(f"Qdrant point {point_id} payload field 'source_name' must be a string.")
        if not isinstance(text, str):
            raise ValueError(f"Qdrant point {point_id} payload field 'text' must be a string.")

        page_number = payload.get("page_number")
        if page_number is not None and not isinstance(page_number, int):
            raise ValueError(f"Qdrant point {point_id} payload field 'page_number' must be an integer.")

        try:
            score = float(getattr(point, "score"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Qdrant point {point_id} has invalid score.") from exc

        return SearchResult(
            chunk_id=str(point_id),
            document_id=document_id,
            source_name=source_name,
            text=text,
            page_number=page_number,
            score=score,
        )

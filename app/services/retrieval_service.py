from __future__ import annotations

from app.schemas.rag import SearchResult
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


class RetrievalService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreService | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    async def retrieve(
        self,
        query: str,
        top_k: int,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        query_vector = await self.embedding_service.embed_query(query)
        return await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            document_id=document_id,
        )

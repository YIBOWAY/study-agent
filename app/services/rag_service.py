from __future__ import annotations

from uuid import uuid4

from app.core.config import Settings, get_settings
from app.services.chunking_service import ChunkingService
from app.services.document_parser_service import DocumentParserService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.prompt_service import RAG_SYSTEM_PROMPT
from app.services.rerank_service import RerankService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService


class RAGService:
    RAG_SYSTEM_PROMPT = RAG_SYSTEM_PROMPT

    def __init__(
        self,
        parser: DocumentParserService | None = None,
        chunker: ChunkingService | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreService | None = None,
        retrieval_service: RetrievalService | None = None,
        rerank_service: RerankService | None = None,
        llm_service: LLMService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.parser = parser or DocumentParserService()
        self.chunker = chunker or ChunkingService(settings=self.settings)
        self.embedding_service = embedding_service or EmbeddingService(settings=self.settings)
        self.vector_store = vector_store or VectorStoreService(settings=self.settings)
        self.retrieval_service = retrieval_service or RetrievalService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )
        self.rerank_service = rerank_service or RerankService(settings=self.settings)
        self.llm_service = llm_service or LLMService()

    async def ingest_pdf(self, file_bytes: bytes, filename: str) -> dict[str, object]:
        document_id = uuid4().hex
        sections = self.parser.parse_pdf(file_bytes, filename)
        chunks = self.chunker.chunk_sections(document_id, filename, sections)
        vectors = await self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        await self.vector_store.ensure_collection()
        await self.vector_store.upsert_chunks(chunks, vectors)
        return {
            "document_id": document_id,
            "filename": filename,
            "chunk_count": len(chunks),
        }

    async def ingest_text(self, text: str, filename: str) -> dict[str, object]:
        from app.schemas.rag import ParsedSection

        document_id = uuid4().hex
        sections = [ParsedSection(text=text, section_title=filename)]
        chunks = self.chunker.chunk_sections(document_id, filename, sections)
        vectors = await self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        await self.vector_store.ensure_collection()
        await self.vector_store.upsert_chunks(chunks, vectors)
        return {
            "document_id": document_id,
            "filename": filename,
            "chunk_count": len(chunks),
        }

    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        retrieved = await self.retrieval_service.retrieve(query=query, top_k=top_k, document_id=document_id)
        reranked = await self.rerank_service.rerank(query=query, candidates=retrieved, final_k=top_k)
        return {
            "results": reranked,
            "embedding_model": self.settings.embedding_model,
            "rerank_model": self.settings.rerank_model,
        }

    async def ask(
        self,
        query: str,
        top_k: int,
        final_k: int,
        document_id: str | None = None,
    ) -> dict[str, object]:
        retrieved = await self.retrieval_service.retrieve(query=query, top_k=top_k, document_id=document_id)
        reranked = await self.rerank_service.rerank(query=query, candidates=retrieved, final_k=final_k)
        context = self.build_context(reranked)
        prompt = f"Question: {query}\n\nContext:\n{context}"
        response = await self.llm_service.chat(
            user_message=prompt,
            system_prompt=self.RAG_SYSTEM_PROMPT,
        )
        return {
            "answer": response["reply"],
            "sources": reranked,
            "model": response["model"],
            "rerank_model": self.settings.rerank_model,
        }

    @staticmethod
    def build_context(results: list[object]) -> str:
        lines: list[str] = []
        for index, result in enumerate(results, start=1):
            page_number = getattr(result, "page_number", None)
            source_name = getattr(result, "source_name", None)
            text = getattr(result, "text", None)
            if isinstance(result, dict):
                page_number = result.get("page_number")
                source_name = result.get("source_name")
                text = result.get("text")

            source_label = str(source_name or "unknown source")
            if page_number is not None:
                lines.append(f"[{index}] {source_label} (page {page_number})")
            else:
                lines.append(f"[{index}] {source_label}")
            lines.append(str(text or ""))

        return "\n".join(lines).strip()

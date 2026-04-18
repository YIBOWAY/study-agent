import pytest

from app.schemas.rag import ChunkRecord, ParsedSection
from app.services.rag_service import RAGService


class FakeParser:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str]] = []

    def parse_pdf(self, file_bytes: bytes, filename: str) -> list[ParsedSection]:
        self.calls.append((file_bytes, filename))
        return [
            ParsedSection(text="First section text", section_title="Intro", page_number=1),
            ParsedSection(text="Second section text", section_title="Body", page_number=2),
        ]


class FakeChunker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[ParsedSection]]] = []

    def chunk_sections(
        self,
        document_id: str,
        filename: str,
        sections: list[ParsedSection],
    ) -> list[ChunkRecord]:
        self.calls.append((document_id, filename, sections))
        return [
            ChunkRecord(
                chunk_id=f"{document_id}-0-0",
                document_id=document_id,
                source_name=filename,
                text="First section text",
                page_number=1,
                section_title="Intro",
            ),
            ChunkRecord(
                chunk_id=f"{document_id}-1-1",
                document_id=document_id,
                source_name=filename,
                text="Second section text",
                page_number=2,
                section_title="Body",
            ),
        ]


class FakeEmbedding:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[0.1, 0.2], [0.3, 0.4]]


class FakeVectorStore:
    def __init__(self) -> None:
        self.ensure_collection_calls = 0
        self.upsert_calls: list[tuple[list[ChunkRecord], list[list[float]]]] = []

    async def ensure_collection(self) -> None:
        self.ensure_collection_calls += 1

    async def upsert_chunks(
        self,
        chunks: list[ChunkRecord],
        vectors: list[list[float]],
    ) -> None:
        self.upsert_calls.append((chunks, vectors))


class FailingVectorStore(FakeVectorStore):
    def __init__(self) -> None:
        super().__init__()
        self.failure = RuntimeError("vector store unavailable")

    async def upsert_chunks(
        self,
        chunks: list[ChunkRecord],
        vectors: list[list[float]],
    ) -> None:
        self.upsert_calls.append((chunks, vectors))
        raise self.failure


class RecordingParser(FakeParser):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    def parse_pdf(self, file_bytes: bytes, filename: str) -> list[ParsedSection]:
        self.events.append("parser")
        return super().parse_pdf(file_bytes, filename)


class RecordingChunker(FakeChunker):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    def chunk_sections(
        self,
        document_id: str,
        filename: str,
        sections: list[ParsedSection],
    ) -> list[ChunkRecord]:
        self.events.append("chunker")
        return super().chunk_sections(document_id, filename, sections)


class RecordingEmbedding(FakeEmbedding):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.events.append("embedder")
        return await super().embed_texts(texts)


class RecordingVectorStore(FakeVectorStore):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    async def ensure_collection(self) -> None:
        self.events.append("ensure_collection")
        await super().ensure_collection()

    async def upsert_chunks(
        self,
        chunks: list[ChunkRecord],
        vectors: list[list[float]],
    ) -> None:
        self.events.append("upsert")
        await super().upsert_chunks(chunks, vectors)


@pytest.mark.asyncio
async def test_ingest_pdf_indexes_chunks() -> None:
    parser = FakeParser()
    chunker = FakeChunker()
    embedding = FakeEmbedding()
    vector_store = FakeVectorStore()
    service = RAGService(
        parser=parser,
        chunker=chunker,
        embedding_service=embedding,
        vector_store=vector_store,
        retrieval_service=object(),
        rerank_service=object(),
        llm_service=object(),
    )

    result = await service.ingest_pdf(b"%PDF-1.4", "guide.pdf")

    assert result["filename"] == "guide.pdf"
    assert result["chunk_count"] == 2
    assert isinstance(result["document_id"], str)
    assert len(result["document_id"]) == 32

    assert parser.calls == [(b"%PDF-1.4", "guide.pdf")]
    assert len(chunker.calls) == 1
    document_id, filename, sections = chunker.calls[0]
    assert document_id == result["document_id"]
    assert filename == "guide.pdf"
    assert [section.text for section in sections] == ["First section text", "Second section text"]

    assert embedding.calls == [["First section text", "Second section text"]]
    assert vector_store.ensure_collection_calls == 1
    assert len(vector_store.upsert_calls) == 1
    chunks, vectors = vector_store.upsert_calls[0]
    assert [chunk.document_id for chunk in chunks] == [result["document_id"], result["document_id"]]
    assert [chunk.text for chunk in chunks] == ["First section text", "Second section text"]
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


@pytest.mark.asyncio
async def test_ingest_pdf_propagates_vector_store_failures() -> None:
    service = RAGService(
        parser=FakeParser(),
        chunker=FakeChunker(),
        embedding_service=FakeEmbedding(),
        vector_store=FailingVectorStore(),
        retrieval_service=object(),
        rerank_service=object(),
        llm_service=object(),
    )

    with pytest.raises(RuntimeError, match="vector store unavailable"):
        await service.ingest_pdf(b"%PDF-1.4", "guide.pdf")


@pytest.mark.asyncio
async def test_ingest_pdf_orchestrates_dependencies_in_order() -> None:
    events: list[str] = []
    service = RAGService(
        parser=RecordingParser(events),
        chunker=RecordingChunker(events),
        embedding_service=RecordingEmbedding(events),
        vector_store=RecordingVectorStore(events),
        retrieval_service=object(),
        rerank_service=object(),
        llm_service=object(),
    )

    await service.ingest_pdf(b"%PDF-1.4", "guide.pdf")

    assert events == ["parser", "chunker", "embedder", "ensure_collection", "upsert"]


def test_rag_service_builds_default_retrieval_with_owned_dependencies() -> None:
    parser = FakeParser()
    chunker = FakeChunker()
    embedding = FakeEmbedding()
    vector_store = FakeVectorStore()

    service = RAGService(
        parser=parser,
        chunker=chunker,
        embedding_service=embedding,
        vector_store=vector_store,
    )

    assert service.parser is parser
    assert service.chunker is chunker
    assert service.embedding_service is embedding
    assert service.vector_store is vector_store
    assert service.retrieval_service.embedding_service is service.embedding_service
    assert service.retrieval_service.vector_store is service.vector_store
    assert service.rerank_service is not None
    assert service.llm_service is not None


class FakeRetrieval:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results
        self.calls: list[tuple[str, int, str | None]] = []

    async def retrieve(self, query: str, top_k: int, document_id: str | None = None) -> list[dict[str, object]]:
        self.calls.append((query, top_k, document_id))
        return self.results


class FakeRerank:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results
        self.calls: list[tuple[str, list[dict[str, object]], int]] = []

    async def rerank(
        self,
        query: str,
        candidates: list[dict[str, object]],
        final_k: int,
    ) -> list[dict[str, object]]:
        self.calls.append((query, candidates, final_k))
        return self.results


class FakeLLM:
    def __init__(self, reply: str, model: str = "test-llm") -> None:
        self.reply = reply
        self.model = model
        self.calls: list[tuple[str, str | None]] = []

    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        self.calls.append((user_message, system_prompt))
        return {"reply": self.reply, "model": self.model}


@pytest.mark.asyncio
async def test_search_reranks_retrieved_chunks() -> None:
    retrieved = [
        {
            "chunk_id": "c1",
            "document_id": "doc-1",
            "source_name": "guide.pdf",
            "text": "Lower ranked candidate",
            "page_number": 1,
            "score": 0.2,
        },
        {
            "chunk_id": "c2",
            "document_id": "doc-1",
            "source_name": "guide.pdf",
            "text": "Best reranked candidate",
            "page_number": 2,
            "score": 0.1,
        },
    ]
    reranked = [retrieved[1], retrieved[0]]
    retrieval = FakeRetrieval(retrieved)
    rerank = FakeRerank(reranked)

    service = RAGService(
        parser=FakeParser(),
        chunker=FakeChunker(),
        embedding_service=FakeEmbedding(),
        vector_store=FakeVectorStore(),
        retrieval_service=retrieval,
        rerank_service=rerank,
        llm_service=FakeLLM("unused"),
    )

    result = await service.search("what changed", top_k=4, document_id="doc-1")

    assert retrieval.calls == [("what changed", 4, "doc-1")]
    assert rerank.calls == [("what changed", retrieved, 4)]
    assert result == {
        "results": reranked,
        "embedding_model": service.settings.embedding_model,
        "rerank_model": service.settings.rerank_model,
    }


@pytest.mark.asyncio
async def test_ask_returns_grounded_answer_and_sources() -> None:
    retrieved = [
        {
            "chunk_id": "c1",
            "document_id": "doc-1",
            "source_name": "guide.pdf",
            "text": "This section explains onboarding.",
            "page_number": 3,
            "score": 0.6,
        },
        {
            "chunk_id": "c2",
            "document_id": "doc-1",
            "source_name": "guide.pdf",
            "text": "This section lists setup steps.",
            "page_number": 4,
            "score": 0.5,
        },
    ]
    reranked = [retrieved[1]]
    retrieval = FakeRetrieval(retrieved)
    rerank = FakeRerank(reranked)
    llm = FakeLLM("Use the setup steps from the guide.", model="test-llm")

    service = RAGService(
        parser=FakeParser(),
        chunker=FakeChunker(),
        embedding_service=FakeEmbedding(),
        vector_store=FakeVectorStore(),
        retrieval_service=retrieval,
        rerank_service=rerank,
        llm_service=llm,
    )

    result = await service.ask("How do I get started?", top_k=5, final_k=1, document_id="doc-1")

    assert retrieval.calls == [("How do I get started?", 5, "doc-1")]
    assert rerank.calls == [("How do I get started?", retrieved, 1)]
    assert llm.calls == [
        (
            "Question: How do I get started?\n\nContext:\n[1] guide.pdf (page 4)\nThis section lists setup steps.",
            service.RAG_SYSTEM_PROMPT,
        )
    ]
    assert result == {
        "answer": "Use the setup steps from the guide.",
        "sources": reranked,
        "model": "test-llm",
        "rerank_model": service.settings.rerank_model,
    }

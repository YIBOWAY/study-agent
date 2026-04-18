import pytest

from app.core.config import Settings
from app.schemas.rag import ParsedSection
from app.services.chunking_service import ChunkingService


def test_rejects_zero_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        ChunkingService(chunk_size=0, chunk_overlap=0)


def test_rejects_negative_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        ChunkingService(chunk_size=-1, chunk_overlap=0)


def test_rejects_negative_chunk_overlap() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be greater than or equal to 0"):
        ChunkingService(chunk_size=20, chunk_overlap=-1)


def test_rejects_overlap_greater_than_or_equal_to_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        ChunkingService(chunk_size=20, chunk_overlap=20)


def test_chunk_sections_skips_whitespace_only_sections() -> None:
    service = ChunkingService(chunk_size=20, chunk_overlap=5)
    sections = [
        ParsedSection(text="   \n\t  ", section_title="Blank", page_number=1),
        ParsedSection(text="Useful content", section_title="Body", page_number=2),
    ]

    chunks = service.chunk_sections("doc-1", "guide.pdf", sections)

    assert len(chunks) == 1
    assert chunks[0].text == "Useful content"
    assert len(chunks[0].chunk_id) == 36  # UUID format
    assert chunks[0].page_number == 2


def test_uses_injected_settings_defaults_when_chunk_values_not_passed() -> None:
    settings = Settings(rag_chunk_size=32, rag_chunk_overlap=8)

    service = ChunkingService(settings=settings)

    assert service.chunk_size == 32
    assert service.chunk_overlap == 8


def test_chunk_sections_exact_boundary_produces_one_chunk() -> None:
    service = ChunkingService(chunk_size=10, chunk_overlap=3)
    sections = [ParsedSection(text="1234567890", section_title="Exact", page_number=1)]

    chunks = service.chunk_sections("doc-1", "guide.pdf", sections)

    assert len(chunks) == 1
    assert chunks[0].text == "1234567890"


def test_chunk_sections_multiple_sections_preserve_metadata_with_stable_ids() -> None:
    service = ChunkingService(chunk_size=8, chunk_overlap=2)
    sections = [
        ParsedSection(text="abcdefghij", section_title="Intro", page_number=1),
        ParsedSection(text="klmnopqrst", section_title="Details", page_number=2),
    ]

    chunks = service.chunk_sections("doc-9", "guide.pdf", sections)

    assert len(chunks) == 4
    assert all(len(c.chunk_id) == 36 for c in chunks)  # UUID format
    assert len(set(c.chunk_id for c in chunks)) == 4  # all unique
    assert [chunk.section_title for chunk in chunks] == ["Intro", "Intro", "Details", "Details"]
    assert [chunk.page_number for chunk in chunks] == [1, 1, 2, 2]
    assert all(chunk.source_name == "guide.pdf" for chunk in chunks)


def test_chunk_sections_final_short_chunk_with_overlap_is_sane() -> None:
    service = ChunkingService(chunk_size=10, chunk_overlap=4)
    sections = [ParsedSection(text="abcdefghijklmnopq", section_title="Tail", page_number=3)]

    chunks = service.chunk_sections("doc-2", "guide.pdf", sections)

    assert [chunk.text for chunk in chunks] == ["abcdefghij", "ghijklmnop", "mnopq"]


def test_chunk_sections_preserve_metadata_and_overlap() -> None:
    service = ChunkingService(chunk_size=20, chunk_overlap=5)
    sections = [
        ParsedSection(
            text="A" * 30,
            section_title="Intro",
            page_number=1,
        )
    ]

    chunks = service.chunk_sections("doc-1", "guide.pdf", sections)

    assert len(chunks) == 2
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].source_name == "guide.pdf"
    assert chunks[0].page_number == 1
    assert chunks[1].text.startswith("AAAAA")

from typing import List, Optional
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.schemas.rag import ChunkRecord, ParsedSection


class ChunkingService:
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.chunk_size = chunk_size if chunk_size is not None else self.settings.rag_chunk_size
        self.chunk_overlap = (
            chunk_overlap if chunk_overlap is not None else self.settings.rag_chunk_overlap
        )
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

    def chunk_sections(
        self,
        document_id: str,
        filename: str,
        sections: List[ParsedSection],
    ) -> List[ChunkRecord]:
        chunks: List[ChunkRecord] = []
        step = self.chunk_size - self.chunk_overlap

        for section_index, section in enumerate(sections):
            text = section.text.strip()
            if not text:
                continue

            for start in range(0, len(text), step):
                chunk_text = text[start : start + self.chunk_size]
                if not chunk_text:
                    continue

                chunks.append(
                    ChunkRecord(
                        chunk_id=str(uuid4()),
                        document_id=document_id,
                        source_name=filename,
                        text=chunk_text,
                        page_number=section.page_number,
                        section_title=section.section_title,
                    )
                )

                if start + self.chunk_size >= len(text):
                    break

        return chunks

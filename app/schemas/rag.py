from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class ParsedSection(BaseModel):
    text: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    source_name: str
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=20, ge=1, le=50)
    document_id: Optional[str] = None


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    source_name: str
    text: str
    page_number: Optional[int] = None
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    embedding_model: str
    rerank_model: Optional[str] = None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=20, ge=1, le=50)
    final_k: int = Field(default=5, ge=1, le=10)
    document_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_final_k(self) -> "AskRequest":
        if self.final_k > self.top_k:
            raise ValueError("final_k must be less than or equal to top_k")
        return self


class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    model: str
    rerank_model: Optional[str] = None


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int

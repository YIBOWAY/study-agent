from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Phase0-1 LLM Backend"
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout: int = 60

    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = Field(default=3072, gt=0)
    embedding_timeout: int = Field(default=60, gt=0)

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "phase2_chunks"

    rerank_api_key: str = ""
    # Rerank will use the existing httpx dependency for Cohere HTTP calls.
    rerank_base_url: str = "https://api.cohere.com/v2"
    rerank_model: str = "rerank-v3.5"

    tavily_api_key: str = ""
    tavily_base_url: str = "https://api.tavily.com"
    enable_code_execution_tool: bool = False

    tool_call_max_iterations: int = Field(default=10, ge=1)
    tool_call_timeout: int = Field(default=30, gt=0)
    research_max_iterations: int = Field(default=3, ge=1, le=10)
    research_top_k: int = Field(default=5, ge=1, le=20)

    rag_chunk_size: int = Field(default=800, gt=0)
    rag_chunk_overlap: int = Field(default=120, ge=0)
    rag_top_k: int = Field(default=20, gt=0)
    rag_final_k: int = Field(default=5, gt=0)

    @field_validator(
        "llm_api_key",
        "embedding_api_key",
        "embedding_base_url",
        "qdrant_api_key",
        "rerank_api_key",
        "tavily_api_key",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized or normalized.startswith("#"):
            return ""
        return normalized

    @model_validator(mode="after")
    def validate_rag_settings(self) -> "Settings":
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError("rag_chunk_overlap must be smaller than rag_chunk_size")
        if self.rag_final_k > self.rag_top_k:
            raise ValueError("rag_final_k must be less than or equal to rag_top_k")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
import os
import shlex
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Agent Platform"
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
    rerank_fail_soft: bool = True

    tavily_api_key: str = ""
    tavily_base_url: str = "https://api.tavily.com"
    enable_code_execution_tool: bool = False

    tool_call_max_iterations: int = Field(default=10, ge=1)
    tool_call_timeout: int = Field(default=30, gt=0)
    research_max_iterations: int = Field(default=3, ge=1, le=10)
    research_top_k: int = Field(default=5, ge=1, le=20)
    memory_data_dir: str = "data/memory"
    memory_max_insights: int = Field(default=100, ge=10, le=1000)
    memory_session_ttl: int = Field(default=3600, ge=60)

    mcp_server_name: str = "research-agent-tools"
    mcp_server_version: str = "0.1.0"
    mcp_external_servers: str = ""

    api_key_required: bool = False
    api_key: str = ""

    guardrails_enabled: bool = True
    guardrails_strict_mode: bool = False
    guardrails_allowed_tools: str = "get_current_time,calculate,search_knowledge_base,web_search,execute_python"
    guardrails_allowed_mcp_tools: str = ""
    tracing_enabled: bool = True
    tracing_db_path: str = "data/traces.db"

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
        "api_key",
        "guardrails_allowed_tools",
        "guardrails_allowed_mcp_tools",
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

    def parse_external_mcp_servers(self) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for raw_entry in self.mcp_external_servers.split("|"):
            entry = raw_entry.strip()
            if not entry or ":" not in entry:
                continue
            raw_name, raw_command = entry.split(":", 1)
            name = raw_name.strip()
            command_line = raw_command.strip()
            if not name or not command_line:
                continue
            parts = [
                self._strip_outer_quotes(part)
                for part in shlex.split(command_line, posix=(os.name != "nt"))
            ]
            if not parts:
                continue
            specs.append({"name": name, "command": parts[0], "args": parts[1:]})
        return specs

    @staticmethod
    def _strip_outer_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_expose_phase2_rag_defaults() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        qdrant_url="http://localhost:6333",
    )

    assert settings.embedding_model == "text-embedding-3-large"
    assert settings.embedding_dimensions == 3072
    assert settings.qdrant_collection == "phase2_chunks"
    assert settings.rag_chunk_size == 800
    assert settings.rag_final_k == 5


def test_rag_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValidationError, match="rag_chunk_overlap must be smaller than rag_chunk_size"):
        Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            qdrant_url="http://localhost:6333",
            rag_chunk_size=100,
            rag_chunk_overlap=100,
        )


def test_rag_final_k_must_not_exceed_top_k() -> None:
    with pytest.raises(ValidationError, match="rag_final_k must be less than or equal to rag_top_k"):
        Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            qdrant_url="http://localhost:6333",
            rag_top_k=5,
            rag_final_k=6,
        )


def test_numeric_rag_settings_require_positive_values() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            llm_api_key="llm-key",
            rerank_api_key="rerank-key",
            qdrant_url="http://localhost:6333",
            embedding_dimensions=0,
        )


def test_rag_chunk_overlap_allows_zero() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        qdrant_url="http://localhost:6333",
        rag_chunk_size=100,
        rag_chunk_overlap=0,
    )

    assert settings.rag_chunk_overlap == 0


def test_comment_only_optional_env_values_are_normalized_to_empty() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        qdrant_url="http://localhost:6333",
        qdrant_api_key="   # 本地 Docker 无密码时留空",
        embedding_base_url="   # 留空时复用 LLM_BASE_URL",
    )

    assert settings.qdrant_api_key == ""
    assert settings.embedding_base_url == ""

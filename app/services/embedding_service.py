from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        api_key = self.settings.embedding_api_key or self.settings.llm_api_key
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY is not configured.")

        base_url = self.settings.embedding_base_url or self.settings.llm_base_url
        url = f"{base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "input": texts,
            "model": self.settings.embedding_model,
        }
        logger.info(
            "Calling embedding API model=%s url=%s input_count=%s",
            self.settings.embedding_model,
            url,
            len(texts),
        )

        is_local = any(
            h in base_url for h in ("localhost", "127.0.0.1", "[::1]")
        )
        async with httpx.AsyncClient(
            timeout=self.settings.embedding_timeout,
            follow_redirects=True,
            trust_env=not is_local,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        response_data = data.get("data")
        if not isinstance(response_data, list):
            raise ValueError("Embedding API response must include a 'data' list.")
        if texts and not response_data:
            raise ValueError("Embedding API returned an empty embeddings list.")
        if len(response_data) != len(texts):
            raise ValueError(
                "Embedding API response returned "
                f"{len(response_data)} embeddings for {len(texts)} inputs."
            )

        embeddings: list[list[float]] = []
        expected_dimensions = self.settings.embedding_dimensions
        for index, item in enumerate(response_data):
            if not isinstance(item, dict) or "embedding" not in item:
                raise ValueError(
                    f"Embedding API response item at index {index} must include an 'embedding' list."
                )

            embedding = item["embedding"]
            if not isinstance(embedding, list):
                raise ValueError(
                    f"Embedding API response item at index {index} has invalid 'embedding'; expected list."
                )
            if len(embedding) != expected_dimensions:
                raise ValueError(
                    "Embedding API response item at index "
                    f"{index} has dimension {len(embedding)}; expected {expected_dimensions}."
                )

            embeddings.append(embedding)

        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self.embed_texts([text])
        if not embeddings:
            raise ValueError("Embedding API returned an empty embeddings list for the query.")
        return embeddings[0]

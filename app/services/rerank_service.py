from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas.rag import SearchResult

logger = logging.getLogger(__name__)


class RerankService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        final_k: int,
    ) -> list[SearchResult]:
        if not candidates:
            return []

        if not self.settings.rerank_api_key:
            raise ValueError("RERANK_API_KEY is not configured.")

        url = f"{self.settings.rerank_base_url.rstrip('/')}/rerank"
        headers = {
            "Authorization": f"Bearer {self.settings.rerank_api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.settings.rerank_model,
            "query": query,
            "documents": [candidate.text for candidate in candidates],
            "top_n": final_k,
        }

        async with httpx.AsyncClient(
            timeout=self.settings.llm_timeout,
            follow_redirects=True,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if self._should_fail_soft(exc):
                    logger.warning(
                        "Rerank provider failed with status=%s; falling back to original candidate order",
                        exc.response.status_code,
                    )
                    return candidates[:final_k]
                raise
            data = response.json()

        results = data.get("results")
        if not isinstance(results, list):
            raise ValueError("Rerank API returned malformed payload: 'results' must be a list.")

        reranked_results: list[SearchResult] = []
        for position, item in enumerate(results):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Rerank API returned malformed payload: results[{position}] must be an object."
                )

            if "index" not in item:
                raise ValueError(
                    f"Rerank API returned malformed payload: results[{position}] is missing 'index'."
                )
            result_index = item["index"]
            if not isinstance(result_index, int) or not 0 <= result_index < len(candidates):
                raise ValueError(
                    f"Rerank API returned invalid candidate index at results[{position}]: {result_index}."
                )

            if "relevance_score" not in item:
                raise ValueError(
                    f"Rerank API returned malformed payload: results[{position}] is missing 'relevance_score'."
                )
            relevance_score = item["relevance_score"]
            if not isinstance(relevance_score, (int, float)):
                raise ValueError(
                    f"Rerank API returned invalid relevance_score at results[{position}]: {relevance_score}."
                )

            candidate = candidates[result_index]
            reranked_results.append(candidate.model_copy(update={"score": float(relevance_score)}))

        return reranked_results

    def _should_fail_soft(self, exc: httpx.HTTPStatusError) -> bool:
        if not self.settings.rerank_fail_soft:
            return False
        status_code = exc.response.status_code
        return status_code in {403, 429} or status_code >= 500

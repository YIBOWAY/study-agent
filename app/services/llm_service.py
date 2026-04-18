from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.prompt_service import CHAT_SYSTEM_PROMPT, EXTRACT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        prompt = system_prompt or CHAT_SYSTEM_PROMPT
        content = await self._call_chat_api(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]
        )
        return {"reply": content, "model": self.settings.llm_model}

    async def extract(self, text: str) -> dict[str, Any]:
        content = await self._call_chat_api(
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Extract structured information from this text:\n{text}",
                },
            ],
            response_format={"type": "json_object"},
        )

        parsed = self._safe_parse_json(content)
        return {
            "summary": str(parsed.get("summary", "")),
            "keywords": self._normalize_keywords(parsed.get("keywords", [])),
            "sentiment": self._normalize_sentiment(parsed.get("sentiment", "neutral")),
            "model": self.settings.llm_model,
        }

    async def _call_chat_api(
        self,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        if not self.settings.llm_api_key:
            raise ValueError("LLM_API_KEY is not configured. Please set it in your .env file.")

        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        logger.info("Calling LLM API model=%s url=%s", self.settings.llm_model, url)

        async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _safe_parse_json(content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse JSON from model output: %s", exc)
            return {
                "summary": content,
                "keywords": [],
                "sentiment": "neutral",
            }

    @staticmethod
    def _normalize_keywords(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @staticmethod
    def _normalize_sentiment(value: Any) -> str:
        sentiment = str(value).lower()
        if sentiment not in {"positive", "neutral", "negative"}:
            return "neutral"
        return sentiment

from __future__ import annotations

import asyncio
import copy
import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import Settings, get_settings
from app.services.prompt_service import CHAT_SYSTEM_PROMPT, EXTRACT_SYSTEM_PROMPT

if TYPE_CHECKING:
    from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        prompt = system_prompt or CHAT_SYSTEM_PROMPT
        message = await self._call_chat_completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]
        )
        content = str(message.get("content") or "").strip()
        return {"reply": content, "model": self.settings.llm_model}

    async def extract(self, text: str) -> dict[str, Any]:
        message = await self._call_chat_completion(
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Extract structured information from this text:\n{text}",
                },
            ],
            response_format={"type": "json_object"},
        )
        content = str(message.get("content") or "")

        parsed = self._safe_parse_json(content)
        return {
            "summary": str(parsed.get("summary", "")),
            "keywords": self._normalize_keywords(parsed.get("keywords", [])),
            "sentiment": self._normalize_sentiment(parsed.get("sentiment", "neutral")),
            "model": self.settings.llm_model,
        }

    async def chat_with_tools(
        self,
        user_message: str,
        tools: list[dict[str, Any]],
        tool_executor: "ToolRegistry",
        max_iterations: int = 5,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        prompt = system_prompt or CHAT_SYSTEM_PROMPT
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ]
        tool_calls_made: list[dict[str, Any]] = []

        for _ in range(max_iterations):
            message = await self._call_chat_completion(messages=messages, tools=tools)
            assistant_message = self._assistant_message_to_payload(message)
            messages.append(assistant_message)

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                content = str(message.get("content") or "").strip()
                return {
                    "reply": content,
                    "model": self.settings.llm_model,
                    "tool_calls_made": tool_calls_made,
                }

            execution_payloads = [
                self._parse_tool_call(tool_call)
                for tool_call in tool_calls
            ]
            execution_results = await asyncio.gather(
                *[
                    self._execute_tool_call(tool_call, tool_executor)
                    for tool_call in execution_payloads
                ]
            )
            for result in execution_results:
                tool_calls_made.append(result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "name": result["tool"],
                        "content": result["content"],
                    }
                )

        return {
            "reply": "Tool call limit reached before a final answer was produced.",
            "model": self.settings.llm_model,
            "tool_calls_made": tool_calls_made,
        }

    async def _call_chat_completion(
        self,
        messages: list[dict[str, Any]],
        response_format: dict[str, str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not self.settings.llm_api_key:
            raise ValueError("LLM_API_KEY is not configured. Please set it in your .env file.")

        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": copy.deepcopy(messages),
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if tools is not None:
            payload["tools"] = tools

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

        return data["choices"][0]["message"]

    @staticmethod
    def _assistant_message_to_payload(message: dict[str, Any]) -> dict[str, Any]:
        payload = {"role": "assistant", "content": message.get("content")}
        if message.get("tool_calls"):
            payload["tool_calls"] = message["tool_calls"]
        return payload

    @staticmethod
    def _parse_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
        function_data = tool_call.get("function") or {}
        arguments_json = function_data.get("arguments") or "{}"
        try:
            arguments = json.loads(arguments_json)
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must decode to an object.")
        except (json.JSONDecodeError, ValueError) as exc:
            arguments = {"_tool_argument_error": str(exc)}
        return {
            "tool_call_id": str(tool_call.get("id") or function_data.get("name") or "tool-call"),
            "tool": str(function_data.get("name") or ""),
            "args": arguments,
        }

    @staticmethod
    async def _execute_tool_call(tool_call: dict[str, Any], tool_executor: "ToolRegistry") -> dict[str, Any]:
        tool_name = tool_call["tool"]
        arguments = tool_call["args"]
        argument_error = arguments.get("_tool_argument_error") if isinstance(arguments, dict) else None
        if argument_error is not None:
            content = json.dumps({"error": f"Invalid tool arguments: {argument_error}"}, ensure_ascii=False)
            return {
                "tool_call_id": tool_call["tool_call_id"],
                "tool": tool_name,
                "args": arguments,
                "result": "",
                "error": f"Invalid tool arguments: {argument_error}",
                "content": content,
            }

        try:
            record = await tool_executor.execute(tool_name, arguments)
        except ValueError as exc:
            content = json.dumps({"error": str(exc)}, ensure_ascii=False)
            return {
                "tool_call_id": tool_call["tool_call_id"],
                "tool": tool_name,
                "args": arguments,
                "result": "",
                "error": str(exc),
                "content": content,
            }

        content = json.dumps(
            {"result": record.result, "error": record.error},
            ensure_ascii=False,
        )
        return {
            "tool_call_id": tool_call["tool_call_id"],
            "tool": record.tool,
            "args": record.args,
            "result": record.result,
            "error": record.error,
            "content": content,
        }

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

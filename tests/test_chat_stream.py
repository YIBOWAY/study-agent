from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import Mock, patch

import pytest

from app.core.config import Settings
from app.services.llm_service import LLMService


class _FakeStreamResponse:
    def __init__(self, lines: list[str], *, status_error: Exception | None = None) -> None:
        self._lines = lines
        self._status_error = status_error

    def raise_for_status(self) -> None:
        if self._status_error is not None:
            raise self._status_error

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line


class _FakeStreamContext:
    def __init__(self, response: _FakeStreamResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeStreamResponse:
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_stream_yields_chunks(mock_client: Any) -> None:
    client_instance = mock_client.return_value.__aenter__.return_value
    client_instance.stream = Mock(return_value=_FakeStreamContext(
        _FakeStreamResponse(
            [
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"delta":{"content":" world"}}]}',
                "data: [DONE]",
            ]
        )
    ))

    service = LLMService(settings=Settings(_env_file=None, llm_api_key="llm-key"))

    chunks = [chunk async for chunk in service.chat_stream("Say hi")]

    assert chunks == ["Hello", " world"]


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_stream_terminates_on_done(mock_client: Any) -> None:
    client_instance = mock_client.return_value.__aenter__.return_value
    client_instance.stream = Mock(return_value=_FakeStreamContext(
        _FakeStreamResponse(
            [
                'data: {"choices":[{"delta":{"content":"Hi"}}]}',
                "data: [DONE]",
                'data: {"choices":[{"delta":{"content":"ignored"}}]}',
            ]
        )
    ))

    service = LLMService(settings=Settings(_env_file=None, llm_api_key="llm-key"))

    chunks = [chunk async for chunk in service.chat_stream("Say hi")]

    assert chunks == ["Hi"]


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_stream_handles_error(mock_client: Any) -> None:
    client_instance = mock_client.return_value.__aenter__.return_value
    client_instance.stream = Mock(side_effect=RuntimeError("stream failed"))

    service = LLMService(settings=Settings(_env_file=None, llm_api_key="llm-key"))

    chunks = [chunk async for chunk in service.chat_stream("Say hi")]

    assert len(chunks) == 1
    assert chunks[0].startswith("[ERROR]")

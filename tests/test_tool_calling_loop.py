from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.services.llm_service import LLMService
from app.services.tool_registry import ToolRegistry


class DummyResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FakeRAGService:
    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [],
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v4.0-pro",
        }


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_with_tools_handles_single_round_tool_call(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.side_effect = [
        DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "calculate",
                                        "arguments": '{"expression": "23 * 47"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ),
        DummyResponse({"choices": [{"message": {"content": "23 * 47 = 1081"}}]}),
    ]
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key")
    service = LLMService(settings=settings)
    registry = ToolRegistry(settings=settings, rag_service=FakeRAGService())

    result = await service.chat_with_tools(
        user_message="Calculate 23 * 47",
        tools=registry.get_openai_tools_schema(["calculate"]),
        tool_executor=registry,
        max_iterations=3,
    )

    assert result["reply"] == "23 * 47 = 1081"
    assert result["tool_calls_made"][0]["tool"] == "calculate"
    assert result["tool_calls_made"][0]["result"] == "1081"
    second_payload = client_instance.post.await_args_list[1].kwargs["json"]
    roles = [message["role"] for message in second_payload["messages"]]
    assert roles[:2] == ["system", "user"]
    assert roles.count("assistant") == 1
    assert roles.count("tool") == 1


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_with_tools_handles_parallel_tool_calls(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.side_effect = [
        DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "calculate",
                                        "arguments": '{"expression": "23 * 47"}',
                                    },
                                },
                                {
                                    "id": "call-2",
                                    "type": "function",
                                    "function": {
                                        "name": "get_current_time",
                                        "arguments": '{"timezone": "UTC"}',
                                    },
                                },
                            ],
                        }
                    }
                ]
            }
        ),
        DummyResponse({"choices": [{"message": {"content": "Done"}}]}),
    ]
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key")
    service = LLMService(settings=settings)
    registry = ToolRegistry(settings=settings, rag_service=FakeRAGService())

    result = await service.chat_with_tools(
        user_message="Do both",
        tools=registry.get_openai_tools_schema(["calculate", "get_current_time"]),
        tool_executor=registry,
        max_iterations=3,
    )

    assert result["reply"] == "Done"
    assert [item["tool"] for item in result["tool_calls_made"]] == ["calculate", "get_current_time"]


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_with_tools_returns_limit_message_when_iterations_exhausted(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.return_value = DummyResponse(
        {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "calculate",
                                    "arguments": '{"expression": "1 + 1"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
    )
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key")
    service = LLMService(settings=settings)
    registry = ToolRegistry(settings=settings, rag_service=FakeRAGService())

    result = await service.chat_with_tools(
        user_message="loop",
        tools=registry.get_openai_tools_schema(["calculate"]),
        tool_executor=registry,
        max_iterations=1,
    )

    assert "limit reached" in result["reply"]
    assert len(result["tool_calls_made"]) == 1


@patch("app.services.llm_service.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_chat_with_tools_reports_tool_argument_error(mock_client: AsyncMock) -> None:
    client_instance = AsyncMock()
    client_instance.post.side_effect = [
        DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "calculate",
                                        "arguments": '{bad-json',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ),
        DummyResponse({"choices": [{"message": {"content": "I saw the tool error."}}]}),
    ]
    mock_client.return_value.__aenter__.return_value = client_instance

    settings = Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key")
    service = LLMService(settings=settings)
    registry = ToolRegistry(settings=settings, rag_service=FakeRAGService())

    result = await service.chat_with_tools(
        user_message="bad args",
        tools=registry.get_openai_tools_schema(["calculate"]),
        tool_executor=registry,
        max_iterations=2,
    )

    assert result["tool_calls_made"][0]["error"] is not None
    second_payload = client_instance.post.await_args_list[1].kwargs["json"]
    roles = [message["role"] for message in second_payload["messages"]]
    assert roles[:2] == ["system", "user"]
    assert roles.count("assistant") == 1
    assert roles.count("tool") == 1

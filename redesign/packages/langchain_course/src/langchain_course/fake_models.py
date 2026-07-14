"""Deterministic LangChain chat models for offline course labs and tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import Field


class DeterministicToolCallingChatModel(BaseChatModel):
    """A real `BaseChatModel` with scripted AIMessage outputs.

    It keeps LangChain message, callback, and tool-binding behavior while making
    the model boundary deterministic and network-free.
    """

    responses: list[AIMessage]
    position: int = 0
    bound_tool_names: list[str] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "deterministic-tool-calling-course-model"

    def bind_tools(
        self,
        tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable[Any, BaseMessage]:
        del tool_choice, kwargs
        self.bound_tool_names = [
            tool.name if isinstance(tool, BaseTool) else str(getattr(tool, "__name__", tool))
            for tool in tools
        ]
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del messages, stop, run_manager, kwargs
        if self.position >= len(self.responses):
            raise RuntimeError("deterministic model has no responses left")
        message = self.responses[self.position]
        self.position += 1
        return ChatResult(generations=[ChatGeneration(message=message)])


def tool_then_final_model(
    *,
    tool_name: str,
    tool_args: dict[str, Any],
    final_text: str,
    call_id: str = "call_offline_1",
) -> DeterministicToolCallingChatModel:
    return DeterministicToolCallingChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": call_id,
                        "name": tool_name,
                        "args": tool_args,
                    }
                ],
            ),
            AIMessage(content=final_text),
        ]
    )

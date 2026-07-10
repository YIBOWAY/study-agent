"""Demo tools for the LangChain track Part 1 agent loop."""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool


@tool
def echo(text: str) -> str:
    """Echo the given text back unchanged. Use for loop demos."""
    return text


@tool
def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def default_demo_tools() -> list[BaseTool]:
    return [echo, add]

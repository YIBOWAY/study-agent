from __future__ import annotations

import os

import pytest
from langchain_course import deepseek as deepseek_mod
from langchain_course.config import DeepSeekSettings
from langchain_course.deepseek import run_hello_chat


def test_build_deepseek_chat_model_passes_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(deepseek_mod, "ChatOpenAI", FakeChatOpenAI)
    settings = DeepSeekSettings(
        api_key="sk-test",
        base_url="https://example.com/v1",
        model="deepseek-chat",
    )
    model = deepseek_mod.build_deepseek_chat_model(settings)
    assert isinstance(model, FakeChatOpenAI)
    assert captured["api_key"] == "sk-test"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["model"] == "deepseek-chat"
    assert captured["temperature"] == 0


@pytest.mark.integration
def test_run_hello_chat_live() -> None:
    if os.environ.get("RUN_DEEPSEEK_TESTS") != "1":
        pytest.skip("set RUN_DEEPSEEK_TESTS=1 and DEEPSEEK_API_KEY to run")
    text = run_hello_chat("Reply with one short word only.")
    assert isinstance(text, str)
    assert text.strip()

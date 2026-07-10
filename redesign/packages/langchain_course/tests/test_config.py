import pytest
from langchain_course.config import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DeepSeekConfigError,
    load_deepseek_settings,
)


def test_load_deepseek_settings_requires_api_key() -> None:
    with pytest.raises(DeepSeekConfigError, match="DEEPSEEK_API_KEY"):
        load_deepseek_settings(environ={})


def test_load_deepseek_settings_uses_defaults() -> None:
    settings = load_deepseek_settings(environ={"DEEPSEEK_API_KEY": "sk-test"})
    assert settings.api_key == "sk-test"
    assert settings.base_url == DEFAULT_DEEPSEEK_BASE_URL
    assert settings.model == DEFAULT_DEEPSEEK_MODEL


def test_load_deepseek_settings_respects_overrides() -> None:
    settings = load_deepseek_settings(
        environ={
            "DEEPSEEK_API_KEY": "sk-test",
            "DEEPSEEK_BASE_URL": "https://example.com/v1",
            "DEEPSEEK_MODEL": "deepseek-reasoner",
        }
    )
    assert settings.base_url == "https://example.com/v1"
    assert settings.model == "deepseek-reasoner"

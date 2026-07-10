from __future__ import annotations

from pathlib import Path

import pytest
from langchain_course.config import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DeepSeekConfigError,
    load_deepseek_settings,
    load_dotenv_files,
)


def test_load_deepseek_settings_requires_api_key() -> None:
    with pytest.raises(DeepSeekConfigError, match="DEEPSEEK_API_KEY"):
        load_deepseek_settings(environ={}, load_dotenv=False)


def test_load_deepseek_settings_uses_defaults() -> None:
    settings = load_deepseek_settings(
        environ={"DEEPSEEK_API_KEY": "sk-test"},
        load_dotenv=False,
    )
    assert settings.api_key == "sk-test"
    assert settings.base_url == DEFAULT_DEEPSEEK_BASE_URL
    assert settings.model == DEFAULT_DEEPSEEK_MODEL


def test_load_deepseek_settings_respects_overrides() -> None:
    settings = load_deepseek_settings(
        environ={
            "DEEPSEEK_API_KEY": "sk-test",
            "DEEPSEEK_BASE_URL": "https://example.com/v1",
            "DEEPSEEK_MODEL": "deepseek-reasoner",
        },
        load_dotenv=False,
    )
    assert settings.base_url == "https://example.com/v1"
    assert settings.model == "deepseek-reasoner"


def test_load_dotenv_files_is_noop_when_environ_injected(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=from-file\n", encoding="utf-8")
    loaded = load_dotenv_files(project_root=tmp_path, environ={})
    assert loaded == []


def test_load_deepseek_settings_reads_dotenv_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text(
        "DEEPSEEK_API_KEY=sk-from-dotenv\nDEEPSEEK_MODEL=deepseek-reasoner\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    settings = load_deepseek_settings(project_root=tmp_path, load_dotenv=True)
    assert settings.api_key == "sk-from-dotenv"
    assert settings.model == "deepseek-reasoner"
    assert settings.base_url == DEFAULT_DEEPSEEK_BASE_URL


def test_process_env_wins_over_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=sk-from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-from-process")
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    settings = load_deepseek_settings(project_root=tmp_path, load_dotenv=True)
    assert settings.api_key == "sk-from-process"

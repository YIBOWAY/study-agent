from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

# redesign/ root: packages/langchain_course/src/langchain_course/config.py → 4 parents up
_PACKAGE_FILE = Path(__file__).resolve()
DEFAULT_PROJECT_ROOT = _PACKAGE_FILE.parents[4]


class DeepSeekConfigError(ValueError):
    """Raised when DeepSeek environment configuration is invalid."""


@dataclass(frozen=True, slots=True)
class DeepSeekSettings:
    api_key: str
    base_url: str
    model: str


def load_dotenv_files(
    *,
    project_root: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[Path]:
    """Load gitignored `.env` files into `os.environ` without overriding existing keys.

    When `environ` is provided (unit tests), this is a no-op so injected maps stay pure.
    Returns the list of files that were found and loaded.
    """
    if environ is not None:
        return []
    try:
        from dotenv import load_dotenv
    except ImportError as exc:  # pragma: no cover - optional group missing
        raise DeepSeekConfigError(
            "python-dotenv is required for .env loading; "
            "run: uv sync --group langchain-course"
        ) from exc

    root = Path(project_root) if project_root is not None else DEFAULT_PROJECT_ROOT
    loaded: list[Path] = []
    for name in (".env", ".env.local"):
        path = root / name
        if path.is_file():
            load_dotenv(path, override=False)
            loaded.append(path)
    return loaded


def load_deepseek_settings(
    *,
    environ: Mapping[str, str] | None = None,
    project_root: str | Path | None = None,
    load_dotenv: bool = True,
) -> DeepSeekSettings:
    """Load DeepSeek settings from process env and optional `.env` files.

    Precedence: already-set process environment variables win over `.env` values.
    Pass `environ={...}` in unit tests to avoid reading real files or process env.
    """
    if load_dotenv and environ is None:
        load_dotenv_files(project_root=project_root, environ=environ)

    env = os.environ if environ is None else environ
    api_key = (env.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise DeepSeekConfigError(
            "DEEPSEEK_API_KEY is required for the LangChain/LangGraph tracks "
            "(set the env var or put it in a local .env file; see .env.example)"
        )
    base_url = (env.get("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL).strip()
    model = (env.get("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL).strip()
    if not base_url:
        raise DeepSeekConfigError("DEEPSEEK_BASE_URL must not be blank when set")
    if not model:
        raise DeepSeekConfigError("DEEPSEEK_MODEL must not be blank when set")
    return DeepSeekSettings(api_key=api_key, base_url=base_url, model=model)

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


class DeepSeekConfigError(ValueError):
    """Raised when DeepSeek environment configuration is invalid."""


@dataclass(frozen=True, slots=True)
class DeepSeekSettings:
    api_key: str
    base_url: str
    model: str


def load_deepseek_settings(*, environ: Mapping[str, str] | None = None) -> DeepSeekSettings:
    env = os.environ if environ is None else environ
    api_key = (env.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise DeepSeekConfigError(
            "DEEPSEEK_API_KEY is required for the LangChain/LangGraph tracks"
        )
    base_url = (env.get("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL).strip()
    model = (env.get("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL).strip()
    if not base_url:
        raise DeepSeekConfigError("DEEPSEEK_BASE_URL must not be blank when set")
    if not model:
        raise DeepSeekConfigError("DEEPSEEK_MODEL must not be blank when set")
    return DeepSeekSettings(api_key=api_key, base_url=base_url, model=model)

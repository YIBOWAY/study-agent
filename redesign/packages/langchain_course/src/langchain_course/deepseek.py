from __future__ import annotations

from langchain_openai import ChatOpenAI

from langchain_course.config import DeepSeekSettings, load_deepseek_settings


def build_deepseek_chat_model(
    settings: DeepSeekSettings | None = None,
) -> ChatOpenAI:
    resolved = load_deepseek_settings() if settings is None else settings
    return ChatOpenAI(
        api_key=resolved.api_key,
        base_url=resolved.base_url,
        model=resolved.model,
        temperature=0,
    )


def run_hello_chat(
    prompt: str = "Reply with exactly: pong",
    *,
    settings: DeepSeekSettings | None = None,
) -> str:
    model = build_deepseek_chat_model(settings)
    message = model.invoke(prompt)
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)

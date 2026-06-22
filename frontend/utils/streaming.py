from __future__ import annotations

from utils.api_client import APIClient


def stream_chat_response(
    client: APIClient,
    message: str,
    system_prompt: str | None = None,
):
    for chunk in client.stream_chat(message=message, system_prompt=system_prompt):
        if chunk:
            yield chunk

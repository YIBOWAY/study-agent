from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings


async def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key_required:
        return

    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="invalid api key")

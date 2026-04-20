from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


async def _get_current_time(arguments: dict[str, Any]) -> str:
    timezone = str(arguments.get("timezone") or "Asia/Shanghai")
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone: {timezone}") from exc

    current_time = datetime.now(zone)
    return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")


def build_get_current_time_tool() -> BuiltinTool:
    return BuiltinTool(
        name="get_current_time",
        description="Get the current date and time for a given timezone.",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone name such as Asia/Shanghai or UTC.",
                }
            },
        },
        handler=_get_current_time,
    )

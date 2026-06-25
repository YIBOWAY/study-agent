from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from research_core.runtime.events import RunEvent


def events_to_records(events: Sequence[RunEvent]) -> list[dict[str, Any]]:
    return [event.to_record() for event in events]


def event_type_sequence(events: Sequence[RunEvent]) -> list[str]:
    return [event.type.value for event in events]

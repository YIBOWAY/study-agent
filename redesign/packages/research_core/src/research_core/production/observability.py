from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.immutability import freeze_json_value, thaw_json_value


@dataclass(frozen=True, slots=True)
class RunDiagnostics:
    run_id: str
    event_count: int
    event_type_counts: Mapping[str, int]
    error_summaries: Sequence[Mapping[str, Any]] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("run_id", self.run_id)
        if (
            not isinstance(self.event_count, int)
            or isinstance(self.event_count, bool)
            or self.event_count < 0
        ):
            raise ValueError("event_count must be a non-negative integer")
        counts = dict(self.event_type_counts)
        for event_type, count in counts.items():
            _require_non_empty("event_type", event_type)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("event_type_counts values must be non-negative integers")
        object.__setattr__(self, "event_type_counts", freeze_json_value(counts))
        object.__setattr__(
            self,
            "error_summaries",
            tuple(freeze_json_value(dict(summary)) for summary in self.error_summaries),
        )

    @classmethod
    def from_events(cls, events: Sequence[RunEvent]) -> RunDiagnostics:
        event_tuple = tuple(events)
        if not event_tuple:
            raise ValueError("events must not be empty")
        if any(not isinstance(event, RunEvent) for event in event_tuple):
            raise ValueError("events must contain RunEvent objects")
        run_id = event_tuple[0].run_id
        if any(event.run_id != run_id for event in event_tuple):
            raise ValueError("events must belong to one run_id")

        counts = Counter(event.type.value for event in event_tuple)
        ordered_counts = {
            event_type.value: counts[event_type.value]
            for event_type in RunEventType
            if counts[event_type.value] > 0
        }
        return cls(
            run_id=run_id,
            event_count=len(event_tuple),
            event_type_counts=ordered_counts,
            error_summaries=tuple(
                _error_summary(event)
                for event in event_tuple
                if event.type is RunEventType.ERROR
            ),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_count": self.event_count,
            "event_type_counts": thaw_json_value(self.event_type_counts),
            "error_summaries": [
                thaw_json_value(summary) for summary in self.error_summaries
            ],
        }


def _error_summary(event: RunEvent) -> dict[str, Any]:
    error = event.payload.get("error", {})
    if not isinstance(error, Mapping):
        error = {}
    kind = error.get("kind", "unknown")
    message = error.get("message", "")
    step = event.payload.get("step", "")
    return {
        "event_id": event.id,
        "step": step,
        "kind": kind if isinstance(kind, str) and kind else "unknown",
        "message": message if isinstance(message, str) else str(message),
    }


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")

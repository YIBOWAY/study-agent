from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from research_core.runtime.events import RunEvent, RunEventType

JSONL_EVENT_LOG_SCHEMA_VERSION = "phase7.run_event_log.v1"


class JsonlRunEventStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if self._path.exists() and self._path.is_dir():
            raise ValueError("path must be a file path")
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: RunEvent) -> None:
        if not isinstance(event, RunEvent):
            raise ValueError("event must be a RunEvent")
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_event_log_record(event), sort_keys=True))
            handle.write("\n")

    def append_many(self, events: Sequence[RunEvent]) -> None:
        for event in events:
            self.append(event)

    def read_run(self, run_id: str) -> tuple[RunEvent, ...]:
        _require_non_empty("run_id", run_id)
        return tuple(event for event in self.read_all() if event.run_id == run_id)

    def read_all(self) -> tuple[RunEvent, ...]:
        if not self._path.exists():
            return ()
        events: list[RunEvent] = []
        for line_number, line in enumerate(
            self._path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            events.append(_event_from_log_line(line, line_number=line_number))
        return tuple(events)

    def list_run_ids(self) -> tuple[str, ...]:
        run_ids: list[str] = []
        seen: set[str] = set()
        for event in self.read_all():
            if event.run_id in seen:
                continue
            seen.add(event.run_id)
            run_ids.append(event.run_id)
        return tuple(run_ids)


def _event_log_record(event: RunEvent) -> dict[str, Any]:
    return {
        "schema_version": JSONL_EVENT_LOG_SCHEMA_VERSION,
        "event": event.to_record(),
    }


def _event_from_log_line(line: str, *, line_number: int) -> RunEvent:
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON event log record at line {line_number}") from exc
    if not isinstance(record, dict):
        raise ValueError(f"event log record at line {line_number} must be an object")
    if record.get("schema_version") != JSONL_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(f"unsupported event log schema at line {line_number}")
    raw_event = record.get("event")
    if not isinstance(raw_event, dict):
        raise ValueError(f"event log record at line {line_number} must contain event")
    try:
        return RunEvent(
            id=raw_event["id"],
            run_id=raw_event["run_id"],
            type=RunEventType(raw_event["type"]),
            payload=raw_event.get("payload", {}),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"invalid event log event at line {line_number}") from exc


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")

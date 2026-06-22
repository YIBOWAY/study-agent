from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid
from typing import Any, AsyncIterator, TypedDict

from app.core.config import Settings

_CURRENT_TRACE_ID: ContextVar[str | None] = ContextVar("current_trace_id", default=None)


class TraceRecord(TypedDict):
    trace_id: str
    parent_id: str | None
    name: str
    started_at: str
    ended_at: str
    latency_ms: float
    status: str
    metadata: dict[str, Any]
    model: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None


@dataclass
class _TraceContext:
    trace_id: str
    parent_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    status: str | None = None

    def set(self, key: str, value: Any) -> None:
        if key == "model":
            self.model = str(value)
        elif key == "prompt_tokens":
            self.prompt_tokens = int(value)
        elif key == "completion_tokens":
            self.completion_tokens = int(value)
        elif key == "cost_usd":
            self.cost_usd = float(value)
        elif key == "status":
            self.status = str(value)
        else:
            self.metadata[key] = value


class TracingService:
    def __init__(self, settings: Settings) -> None:
        self.db_path = Path(settings.tracing_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    model TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    cost_usd REAL
                )
                """
            )
            conn.commit()

    @asynccontextmanager
    async def trace(self, name: str, metadata: dict[str, Any] | None = None) -> AsyncIterator[_TraceContext]:
        parent_id = _CURRENT_TRACE_ID.get()
        trace_id = str(uuid.uuid4())
        token = _CURRENT_TRACE_ID.set(trace_id)
        started = datetime.now(timezone.utc)
        ctx = _TraceContext(
            trace_id=trace_id,
            parent_id=parent_id,
            metadata=dict(metadata or {}),
        )

        try:
            yield ctx
        except Exception as exc:
            ctx.status = "error"
            ctx.metadata["error_message"] = str(exc)
            raise
        finally:
            ended = datetime.now(timezone.utc)
            await self._insert_record(
                {
                    "trace_id": trace_id,
                    "parent_id": parent_id,
                    "name": name,
                    "started_at": started.replace(microsecond=0).isoformat(),
                    "ended_at": ended.replace(microsecond=0).isoformat(),
                    "latency_ms": (ended - started).total_seconds() * 1000,
                    "status": ctx.status or "ok",
                    "metadata": ctx.metadata,
                    "model": ctx.model,
                    "prompt_tokens": ctx.prompt_tokens,
                    "completion_tokens": ctx.completion_tokens,
                    "cost_usd": ctx.cost_usd,
                }
            )
            _CURRENT_TRACE_ID.reset(token)

    async def query_traces(self, limit: int = 100, name: str | None = None) -> list[TraceRecord]:
        query = "SELECT * FROM traces"
        params: list[Any] = []
        if name is not None:
            query += " WHERE name = ?"
            params.append(name)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        rows = await asyncio.to_thread(self._fetch_rows, query, params)
        return [self._row_to_record(row) for row in rows]

    async def get_cost_summary(self, since: str | None = None) -> dict[str, Any]:
        query = "SELECT * FROM traces"
        params: list[Any] = []
        if since is not None:
            query += " WHERE started_at >= ?"
            params.append(since)
        rows = await asyncio.to_thread(self._fetch_rows, query, params)
        records = [self._row_to_record(row) for row in rows if row["cost_usd"] is not None]

        total_cost = sum(float(record["cost_usd"] or 0.0) for record in records)
        total_calls = len(records)
        total_prompt = sum(int(record["prompt_tokens"] or 0) for record in records)
        total_completion = sum(int(record["completion_tokens"] or 0) for record in records)
        by_model: dict[str, dict[str, Any]] = {}

        for record in records:
            model = record["model"] or "unknown"
            bucket = by_model.setdefault(
                model,
                {"calls": 0, "cost": 0.0, "tokens": {"prompt": 0, "completion": 0}},
            )
            bucket["calls"] += 1
            bucket["cost"] += float(record["cost_usd"] or 0.0)
            bucket["tokens"]["prompt"] += int(record["prompt_tokens"] or 0)
            bucket["tokens"]["completion"] += int(record["completion_tokens"] or 0)

        return {
            "total_cost_usd": round(total_cost, 10),
            "total_calls": total_calls,
            "total_tokens": {"prompt": total_prompt, "completion": total_completion},
            "by_model": by_model,
            "since": since or "",
        }

    async def query_agent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        root_rows = await asyncio.to_thread(
            self._fetch_rows,
            "SELECT * FROM traces WHERE name = ? ORDER BY started_at DESC LIMIT ?",
            ["agent_run", limit],
        )
        roots = [self._row_to_record(row) for row in root_rows]
        if not roots:
            return []

        root_ids = [root["trace_id"] for root in roots]
        placeholders = ",".join("?" for _ in root_ids)
        child_rows = await asyncio.to_thread(
            self._fetch_rows,
            f"SELECT * FROM traces WHERE parent_id IN ({placeholders}) ORDER BY started_at ASC",
            root_ids,
        )
        children_by_parent: dict[str, list[TraceRecord]] = {root_id: [] for root_id in root_ids}
        for row in child_rows:
            record = self._row_to_record(row)
            parent_id = record["parent_id"]
            if parent_id is not None:
                children_by_parent.setdefault(parent_id, []).append(record)

        return [
            {"root": root, "children": children_by_parent.get(root["trace_id"], [])}
            for root in roots
        ]

    async def _insert_record(self, record: TraceRecord) -> None:
        async with self._lock:
            await asyncio.to_thread(self._insert_record_sync, record)

    def _insert_record_sync(self, record: TraceRecord) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO traces (
                    trace_id, parent_id, name, started_at, ended_at, latency_ms,
                    status, metadata, model, prompt_tokens, completion_tokens, cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["trace_id"],
                    record["parent_id"],
                    record["name"],
                    record["started_at"],
                    record["ended_at"],
                    record["latency_ms"],
                    record["status"],
                    json.dumps(record["metadata"], ensure_ascii=False),
                    record["model"],
                    record["prompt_tokens"],
                    record["completion_tokens"],
                    record["cost_usd"],
                ),
            )
            conn.commit()

    def _fetch_rows(self, query: str, params: list[Any]) -> list[sqlite3.Row]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> TraceRecord:
        return {
            "trace_id": str(row["trace_id"]),
            "parent_id": str(row["parent_id"]) if row["parent_id"] is not None else None,
            "name": str(row["name"]),
            "started_at": str(row["started_at"]),
            "ended_at": str(row["ended_at"]),
            "latency_ms": float(row["latency_ms"]),
            "status": str(row["status"]),
            "metadata": json.loads(str(row["metadata"])) if row["metadata"] else {},
            "model": str(row["model"]) if row["model"] is not None else None,
            "prompt_tokens": int(row["prompt_tokens"]) if row["prompt_tokens"] is not None else None,
            "completion_tokens": int(row["completion_tokens"]) if row["completion_tokens"] is not None else None,
            "cost_usd": float(row["cost_usd"]) if row["cost_usd"] is not None else None,
        }

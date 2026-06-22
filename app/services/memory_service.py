from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from typing import TypedDict

from app.core.config import Settings, get_settings


class SessionMemory(TypedDict):
    session_id: str
    created_at: str
    last_accessed: str
    topics: list[str]
    insights: list[str]
    total_queries: int


class InsightRecord(TypedDict):
    topic: str
    insight: str
    source_count: int
    created_at: str
    session_id: str


class MemoryService:
    def __init__(
        self,
        data_dir: str | None = None,
        max_insights: int | None = None,
        session_ttl: int | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.data_dir = Path(data_dir or self.settings.memory_data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_insights = max_insights or self.settings.memory_max_insights
        self.session_ttl = session_ttl or self.settings.memory_session_ttl
        self._lock = asyncio.Lock()
        self._sessions: dict[str, SessionMemory] = {}
        self._long_term_path = self.data_dir / "long_term.json"
        self._insights = self._load_initial_insights()

    async def add_session_context(self, session_id: str, topic: str, insights: list[str]) -> None:
        if not session_id:
            return

        session = self._sessions.get(session_id)
        now = _timestamp()
        if session is None or _is_expired(session["last_accessed"], self.session_ttl):
            session = {
                "session_id": session_id,
                "created_at": now,
                "last_accessed": now,
                "topics": [],
                "insights": [],
                "total_queries": 0,
            }

        if not session["topics"] or session["topics"][-1] != topic:
            session["topics"].append(topic)
        for insight in insights:
            cleaned = insight.strip()
            if cleaned:
                session["insights"].append(cleaned)
        session["total_queries"] += 1
        session["last_accessed"] = now
        self._sessions[session_id] = session

    async def get_session_context(self, session_id: str) -> SessionMemory | None:
        if not session_id:
            return None

        session = self._sessions.get(session_id)
        if session is None:
            return None
        if _is_expired(session["last_accessed"], self.session_ttl):
            self._sessions.pop(session_id, None)
            return None

        session["last_accessed"] = _timestamp()
        return deepcopy(session)

    async def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def save_insight(
        self,
        topic: str,
        insight: str,
        source_count: int,
        session_id: str,
    ) -> None:
        record: InsightRecord = {
            "topic": topic.strip(),
            "insight": insight.strip(),
            "source_count": source_count,
            "created_at": _timestamp(),
            "session_id": session_id,
        }
        self._insights.append(record)
        if len(self._insights) > self.max_insights:
            self._insights = self._insights[-self.max_insights :]
        await self._persist_insights()

    async def retrieve_relevant_insights(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[InsightRecord]:
        query_terms = _tokenize(query)
        if not query_terms:
            return []

        scored: list[tuple[int, InsightRecord]] = []
        for record in self._insights:
            haystack_terms = _tokenize(f"{record['topic']} {record['insight']}")
            overlap = len(query_terms & haystack_terms)
            if overlap > 0:
                scored.append((overlap, record))

        scored.sort(key=lambda item: (item[0], item[1]["created_at"]), reverse=True)
        return [deepcopy(record) for _, record in scored[:top_k]]

    async def get_all_insights(self) -> list[InsightRecord]:
        return deepcopy(self._insights)

    async def clear_all_insights(self) -> int:
        deleted_count = len(self._insights)
        self._insights = []
        await self._persist_insights()
        return deleted_count

    def _load_initial_insights(self) -> list[InsightRecord]:
        if not self._long_term_path.exists():
            return []
        try:
            payload = json.loads(self._long_term_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        records: list[InsightRecord] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            topic = str(item.get("topic") or "").strip()
            insight = str(item.get("insight") or "").strip()
            created_at = str(item.get("created_at") or "").strip()
            session_id = str(item.get("session_id") or "")
            source_count = int(item.get("source_count") or 0)
            if not topic or not insight or not created_at:
                continue
            records.append(
                {
                    "topic": topic,
                    "insight": insight,
                    "source_count": source_count,
                    "created_at": created_at,
                    "session_id": session_id,
                }
            )
        return records[-self.max_insights :]

    async def _persist_insights(self) -> None:
        payload = json.dumps(self._insights, ensure_ascii=False, indent=2)
        async with self._lock:
            await asyncio.to_thread(self._long_term_path.write_text, payload, encoding="utf-8")


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_expired(last_accessed: str, session_ttl: int) -> bool:
    try:
        last_seen = datetime.fromisoformat(last_accessed)
    except ValueError:
        return True
    return datetime.now(timezone.utc) - last_seen > timedelta(seconds=session_ttl)


def _tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))

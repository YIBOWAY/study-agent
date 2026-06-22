from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class FakeMemoryService:
    def __init__(self) -> None:
        self.cleared_sessions: list[str] = []
        self.cleared_all = 0
        self.insights = [
            {
                "topic": "RAG chunking",
                "insight": "Chunk overlap improves boundary recall.",
                "source_count": 2,
                "created_at": "2026-04-21T00:00:00+00:00",
                "session_id": "session-1",
            }
        ]
        self.session = {
            "session_id": "session-1",
            "created_at": "2026-04-21T00:00:00+00:00",
            "last_accessed": "2026-04-21T00:00:00+00:00",
            "topics": ["RAG chunking"],
            "insights": ["Chunk overlap improves boundary recall."],
            "total_queries": 1,
        }

    async def get_all_insights(self) -> list[dict[str, object]]:
        return self.insights

    async def retrieve_relevant_insights(self, query: str, top_k: int = 3) -> list[dict[str, object]]:
        if "chunking" in query:
            return self.insights
        return []

    async def get_session_context(self, session_id: str) -> dict[str, object] | None:
        if session_id == "session-1":
            return self.session
        return None

    async def clear_session(self, session_id: str) -> None:
        self.cleared_sessions.append(session_id)

    async def clear_all_insights(self) -> int:
        self.cleared_all += 1
        deleted = len(self.insights)
        self.insights = []
        return deleted


def test_get_insights_empty() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    fake_memory.insights = []
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.get("/api/v1/memory/insights")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json() == {"insights": [], "total": 0}


def test_get_insights_after_save() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.get("/api/v1/memory/insights")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_search_insights() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.get("/api/v1/memory/insights/search", params={"query": "chunking"})
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json()["query"] == "chunking"
    assert len(response.json()["insights"]) == 1


def test_get_session() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.get("/api/v1/memory/sessions/session-1")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json()["session_id"] == "session-1"


def test_get_session_not_found() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.get("/api/v1/memory/sessions/missing")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 404


def test_clear_session() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.delete("/api/v1/memory/sessions/session-1")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json()["status"] == "cleared"
    assert fake_memory.cleared_sessions == ["session-1"]


def test_clear_all_insights() -> None:
    import app.api.routes.memory as memory_route

    fake_memory = FakeMemoryService()
    original = memory_route.memory_service
    memory_route.memory_service = fake_memory
    try:
        response = client.delete("/api/v1/memory/insights")
    finally:
        memory_route.memory_service = original

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1

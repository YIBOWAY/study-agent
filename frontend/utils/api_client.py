from __future__ import annotations

import json
import os
from typing import Any

import httpx


DEFAULT_TIMEOUT = 120.0


class APIError(RuntimeError):
    pass


class APIClient:
    def __init__(self, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")
        self.timeout = timeout

    def ingest_file(self, upload: Any) -> dict[str, Any]:
        if upload is None:
            raise APIError("No file selected.")
        upload.seek(0)
        files = {
            "file": (
                upload.name,
                upload.getvalue(),
                upload.type or "application/octet-stream",
            )
        }
        return self._request("POST", "/api/v1/rag/ingest", files=files)

    def ask_rag(
        self,
        query: str,
        top_k: int,
        final_k: int,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "query": query,
            "top_k": top_k,
            "final_k": final_k,
            "document_id": document_id,
        }
        return self._request("POST", "/api/v1/rag/ask", json=payload)

    def run_research(
        self,
        topic: str,
        mode: str,
        max_iterations: int,
        top_k: int,
        session_id: str,
    ) -> dict[str, Any]:
        payload = {
            "topic": topic,
            "mode": mode,
            "max_iterations": max_iterations,
            "top_k": top_k,
            "session_id": session_id,
        }
        return self._request("POST", "/api/v1/research", json=payload)

    def get_traces(self, limit: int = 20, name: str | None = None) -> dict[str, Any]:
        params = {"limit": limit}
        if name:
            params["name"] = name
        return self._request("GET", "/api/v1/observability/traces", params=params)

    def get_cost(self, since: str | None = None) -> dict[str, Any]:
        params = {"since": since} if since else None
        return self._request("GET", "/api/v1/observability/cost", params=params)

    def get_agent_runs(self, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", "/api/v1/observability/agent_runs", params={"limit": limit})

    def stream_chat(self, message: str, system_prompt: str | None = None):
        payload = {"message": message, "system_prompt": system_prompt}
        with httpx.stream(
            "POST",
            f"{self.base_url}/api/v1/chat/stream",
            json=payload,
            timeout=self.timeout,
            headers={"Accept": "text/event-stream"},
        ) as response:
            self._raise_for_status(response)
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    parsed = json.loads(data)
                except json.JSONDecodeError as exc:
                    raise APIError(f"Invalid stream payload: {data}") from exc
                yield str(parsed.get("content", ""))

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.request(method, path, **kwargs)
            self._raise_for_status(response)
            return response.json()
        except httpx.HTTPError as exc:
            raise APIError(str(exc)) from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("detail", detail)
            except ValueError:
                pass
            raise APIError(f"{response.status_code}: {detail}") from exc

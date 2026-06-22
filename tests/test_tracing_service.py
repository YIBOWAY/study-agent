from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.tracing_service import TracingService


def _build_service(tmp_path: Path) -> TracingService:
    settings = Settings(tracing_db_path=str(tmp_path / "traces.db"))
    return TracingService(settings)


@pytest.mark.asyncio
async def test_trace_records_basic(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async with service.trace("llm_chat", {"model": "gpt-5.4"}) as ctx:
        ctx.set("model", "gpt-5.4")
        ctx.set("prompt_tokens", 100)
        ctx.set("completion_tokens", 50)
        ctx.set("cost_usd", 0.00125)

    traces = await service.query_traces(limit=10)

    assert len(traces) == 1
    assert traces[0]["name"] == "llm_chat"
    assert traces[0]["model"] == "gpt-5.4"
    assert traces[0]["prompt_tokens"] == 100
    assert traces[0]["completion_tokens"] == 50
    assert traces[0]["cost_usd"] == 0.00125


@pytest.mark.asyncio
async def test_trace_with_parent(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async with service.trace("agent_run"):
        async with service.trace("llm_chat"):
            pass

    traces = await service.query_traces(limit=10)
    by_name = {item["name"]: item for item in traces}

    assert by_name["llm_chat"]["parent_id"] == by_name["agent_run"]["trace_id"]


@pytest.mark.asyncio
async def test_trace_records_error(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    with pytest.raises(RuntimeError, match="boom"):
        async with service.trace("tool_execute"):
            raise RuntimeError("boom")

    traces = await service.query_traces(limit=10)

    assert traces[0]["name"] == "tool_execute"
    assert traces[0]["status"] == "error"
    assert traces[0]["metadata"]["error_message"] == "boom"


@pytest.mark.asyncio
async def test_query_traces_filters_by_name(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async with service.trace("llm_chat"):
        pass
    async with service.trace("tool_execute"):
        pass

    traces = await service.query_traces(limit=10, name="tool_execute")

    assert len(traces) == 1
    assert traces[0]["name"] == "tool_execute"


@pytest.mark.asyncio
async def test_cost_summary_aggregates(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    async with service.trace("llm_chat") as ctx:
        ctx.set("model", "gpt-5.4")
        ctx.set("prompt_tokens", 100)
        ctx.set("completion_tokens", 50)
        ctx.set("cost_usd", 0.00125)
    async with service.trace("llm_chat") as ctx:
        ctx.set("model", "gpt-4o-mini")
        ctx.set("prompt_tokens", 200)
        ctx.set("completion_tokens", 100)
        ctx.set("cost_usd", 0.00009)

    summary = await service.get_cost_summary()

    assert summary["total_cost_usd"] == pytest.approx(0.00134)
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == {"prompt": 300, "completion": 150}
    assert summary["by_model"]["gpt-5.4"]["calls"] == 1
    assert summary["by_model"]["gpt-4o-mini"]["tokens"] == {"prompt": 200, "completion": 100}

from __future__ import annotations

import json

import pytest

from app.services.evaluation_service import (
    llm_judge_answer_relevance,
    llm_judge_context_precision,
    llm_judge_faithfulness,
)


@pytest.mark.asyncio
async def test_faithfulness_full_support() -> None:
    calls: list[str] = []

    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        calls.append(prompt)
        if len(calls) == 1:
            return {"reply": json.dumps({"claims": ["Phase 7 adds guardrails.", "Phase 7 adds tracing."]})}
        return {"reply": json.dumps({"supported": True, "reasoning": "supported"})}

    result = await llm_judge_faithfulness(
        "What does Phase 7 add?",
        "Phase 7 adds guardrails and tracing.",
        ["Phase 7 adds guardrails and tracing."],
        judge,
    )

    assert result["score"] == 1.0
    assert result["supported"] == 2
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_faithfulness_partial() -> None:
    support = iter([True, False])

    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        if "Extract atomic factual claims" in prompt:
            return {"reply": json.dumps({"claims": ["Supported claim", "Unsupported claim"]})}
        return {"reply": json.dumps({"supported": next(support), "reasoning": "checked"})}

    result = await llm_judge_faithfulness("q", "a", ["context"], judge)

    assert result["score"] == 0.5
    assert result["supported"] == 1
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_faithfulness_parse_failure() -> None:
    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        return {"reply": "not json"}

    result = await llm_judge_faithfulness("q", "a", ["context"], judge)

    assert result["score"] == 0.0
    assert result["reasoning"] == "parse_failed"


@pytest.mark.asyncio
async def test_context_precision_basic() -> None:
    responses = iter([
        {"relevant": True, "reasoning": "matches"},
        {"relevant": False, "reasoning": "off topic"},
    ])

    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        return {"reply": json.dumps(next(responses))}

    result = await llm_judge_context_precision("q", ["relevant context", "noise"], judge)

    assert result == {"score": 0.5, "relevant": 1, "total": 2}


@pytest.mark.asyncio
async def test_answer_relevance_high_score() -> None:
    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        return {"reply": json.dumps({"score": 5, "reasoning": "direct answer"})}

    result = await llm_judge_answer_relevance("q", "answer", judge)

    assert result == {"score": 1.0, "raw_score": 5, "reasoning": "direct answer"}


@pytest.mark.asyncio
async def test_answer_relevance_low_score() -> None:
    async def judge(prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        return {"reply": json.dumps({"score": 1, "reasoning": "unrelated"})}

    result = await llm_judge_answer_relevance("q", "answer", judge)

    assert result == {"score": 0.2, "raw_score": 1, "reasoning": "unrelated"}

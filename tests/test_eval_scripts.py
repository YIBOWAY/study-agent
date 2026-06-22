from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.run_agent_eval import run_agent_evaluation
from scripts.run_rag_eval import run_rag_evaluation


@pytest.mark.asyncio
async def test_run_agent_evaluation_builds_mode_specific_runner(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    import scripts.run_agent_eval as module

    monkeypatch.setattr(module, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(
        module,
        "load_agent_cases",
        lambda path: [
            {
                "topic": "Phase 7",
                "expected_keywords": ["evaluation"],
                "mode": "agent_v2",
                "max_iterations": 2,
            }
        ],
    )

    captured: dict[str, Any] = {}

    async def fake_workflow(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {
            "report": "workflow report",
            "iterations_used": 1,
            "search_result_count": 2,
        }

    async def fake_batch(cases: list[dict[str, Any]], run_fn: Any, **kwargs: Any) -> dict[str, Any]:
        await run_fn(topic="Phase 7", max_iterations=2, top_k=5)
        return {"total": len(cases), "completed_count": 1, "success_rate": 1.0, "per_case": []}

    monkeypatch.setattr(module, "run_workflow", fake_workflow)
    monkeypatch.setattr(module, "evaluate_agent_batch", fake_batch)

    result = await run_agent_evaluation("workflow", 1)

    assert result["total"] == 1
    assert captured["topic"] == "Phase 7"
    assert captured["max_iterations"] == 2
    assert captured["top_k"] == 5
    assert "memory_service" not in captured
    assert "session_id" not in captured


@pytest.mark.asyncio
async def test_run_rag_evaluation_with_llm_judge_uses_new_metrics(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    import scripts.run_rag_eval as module

    class DummyCase:
        def __init__(self, question: str) -> None:
            self.question = question
            self.document_id = None

    class DummyRAGService:
        def __init__(self) -> None:
            self.search_calls: list[str] = []
            self.ask_calls: list[str] = []

        async def search(self, question: str, top_k: int, document_id: str | None = None) -> dict[str, Any]:
            self.search_calls.append(question)
            return {"results": [{"text": f"context for {question}"}]}

        async def ask(
            self,
            question: str,
            top_k: int,
            final_k: int,
            document_id: str | None = None,
        ) -> dict[str, Any]:
            self.ask_calls.append(question)
            return {
                "answer": f"answer for {question}",
                "sources": [{"text": f"source for {question}"}],
            }

        @staticmethod
        def build_context(sources: list[dict[str, str]]) -> str:
            return "\n".join(source["text"] for source in sources)

    class DummyLLMService:
        async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
            return {"reply": "{}"}

    monkeypatch.setattr(module, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(module, "load_eval_cases", lambda path: [DummyCase("q1"), DummyCase("q2"), DummyCase("q3")])
    monkeypatch.setattr(module, "RAGService", DummyRAGService)
    monkeypatch.setattr(module, "LLMService", DummyLLMService, raising=False)
    monkeypatch.setattr(module, "compute_retrieval_hit_rate", lambda cases, batches: 1.0)
    monkeypatch.setattr(module, "compute_citation_usefulness", lambda answers, source_counts: {"citation_presence": 1.0})
    monkeypatch.setattr(module, "llm_judge_faithfulness", _async_result({"score": 0.75}))
    monkeypatch.setattr(module, "llm_judge_context_precision", _async_result({"score": 0.5}))
    monkeypatch.setattr(module, "llm_judge_answer_relevance", _async_result({"score": 1.0}))

    result = await run_rag_evaluation(limit=2, with_llm_judge=True)

    assert result["total_cases"] == 2
    assert result["faithfulness"]["avg_score"] == 0.75
    assert result["context_precision"]["avg_score"] == 0.5
    assert result["answer_relevance"]["avg_score"] == 1.0


def _async_result(payload: dict[str, Any]) -> Any:
    async def _inner(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return payload

    return _inner

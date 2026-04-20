import json
import sys
from types import SimpleNamespace

import pytest

from scripts import run_rag_eval


class FakeRAGService:
    source: dict[str, object] = {}

    def __init__(self) -> None:
        self.source = type(self).source

    @staticmethod
    def build_context(results: list[object]) -> str:
        lines: list[str] = []
        for index, result in enumerate(results, start=1):
            item = dict(result)
            source_name = str(item.get("source_name") or "unknown source")
            page_number = item.get("page_number")
            if page_number is not None:
                lines.append(f"[{index}] {source_name} (page {page_number})")
            else:
                lines.append(f"[{index}] {source_name}")
            lines.append(str(item.get("text") or ""))
        return "\n".join(lines).strip()

    async def search(self, query: str, top_k: int, document_id: str | None = None) -> dict[str, object]:
        return {
            "results": [self.source],
            "embedding_model": "text-embedding-3-large",
            "rerank_model": "rerank-v3.5",
        }

    async def ask(
        self,
        query: str,
        top_k: int,
        final_k: int,
        document_id: str | None = None,
    ) -> dict[str, object]:
        return {
            "answer": "Revenue grew 20% year over year. [1]",
            "sources": [self.source],
            "model": "gpt-5.4",
            "rerank_model": "rerank-v3.5",
        }


class FakeLLMService:
    async def chat(self, user_message: str, system_prompt: str | None = None) -> dict[str, str]:
        return {"reply": "supported", "model": "gpt-5.4"}


@pytest.mark.asyncio
async def test_run_rag_eval_rebuilds_context_from_sources_for_judge(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "source_name": "guide.pdf",
        "text": "Revenue grew 20% year over year.",
        "page_number": 2,
        "score": 0.97,
    }
    cases = [SimpleNamespace(question="How did revenue change?", document_id="doc-1")]

    monkeypatch.setattr(run_rag_eval, "load_eval_cases", lambda path: cases)
    FakeRAGService.source = source
    monkeypatch.setattr(run_rag_eval, "RAGService", FakeRAGService)
    monkeypatch.setattr(run_rag_eval, "compute_retrieval_hit_rate", lambda loaded_cases, batches: 1.0)
    monkeypatch.setattr(run_rag_eval, "compute_citation_usefulness", lambda answers, source_counts: 1.0)

    async def fake_compute_answer_correctness(loaded_cases, answers, judge_fn) -> float:
        return 1.0

    async def fake_compute_groundedness(answers, contexts, judge_fn) -> float:
        assert contexts == ["[1] guide.pdf (page 2)\nRevenue grew 20% year over year."]
        return 1.0

    monkeypatch.setattr(run_rag_eval, "compute_answer_correctness", fake_compute_answer_correctness)
    monkeypatch.setattr(run_rag_eval, "compute_groundedness", fake_compute_groundedness)

    import app.services.llm_service as llm_service_module

    monkeypatch.setattr(llm_service_module, "LLMService", FakeLLMService)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_rag_eval",
            "--cases",
            "eval/sample_questions.jsonl",
            "--top-k",
            "20",
            "--final-k",
            "5",
            "--judge",
        ],
    )

    await run_rag_eval.main()

    output = json.loads(capsys.readouterr().out)
    assert output["total_cases"] == 1
    assert output["groundedness"] == 1.0

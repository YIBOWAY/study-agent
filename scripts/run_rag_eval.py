from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.evaluation_service import (
    compute_citation_usefulness,
    compute_retrieval_hit_rate,
    llm_judge_answer_relevance,
    llm_judge_context_precision,
    llm_judge_faithfulness,
    load_eval_cases,
    panel_judge,
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

RESULTS_DIR = Path("eval/results")


async def run_rag_evaluation(
    *,
    cases_path: str | Path = "eval/sample_questions.jsonl",
    limit: int | None = None,
    top_k: int = 20,
    final_k: int = 5,
    with_llm_judge: bool = False,
    panel_size: int = 1,
) -> dict[str, Any]:
    cases = load_eval_cases(Path(cases_path))
    if limit is not None:
        cases = cases[:limit]
    service = RAGService()

    search_batches: list[list[object]] = []
    answers: list[str] = []
    contexts: list[str] = []
    context_lists: list[list[str]] = []
    source_counts: list[int] = []

    for case in cases:
        search_result = await service.search(
            case.question, top_k=top_k, document_id=case.document_id,
        )
        search_batches.append(search_result["results"])
        context_lists.append([_extract_result_text(item) for item in search_result["results"]])

        ask_result = await service.ask(
            case.question,
            top_k=top_k,
            final_k=final_k,
            document_id=case.document_id,
        )
        answers.append(ask_result["answer"])
        contexts.append(RAGService.build_context(ask_result["sources"]))
        source_counts.append(len(ask_result["sources"]))

    summary: dict[str, Any] = {
        "total_cases": len(cases),
        "top_k": top_k,
        "final_k": final_k,
        "retrieval_hit_rate": compute_retrieval_hit_rate(cases, search_batches),
        "citation": compute_citation_usefulness(answers, source_counts),
    }

    if with_llm_judge:
        llm = LLMService()
        faithfulness_results = []
        context_precision_results = []
        answer_relevance_results = []
        for case, answer, source_contexts, retrieved_contexts in zip(
            cases,
            answers,
            [list(filter(None, context.split("\n\n"))) if context else [] for context in contexts],
            context_lists,
        ):
            faithfulness_results.append(
                await panel_judge(
                    llm_judge_faithfulness,
                    case.question,
                    answer,
                    source_contexts,
                    llm.chat,
                    panel_size=panel_size,
                )
            )
            context_precision_results.append(
                await panel_judge(
                    llm_judge_context_precision,
                    case.question,
                    retrieved_contexts,
                    llm.chat,
                    panel_size=panel_size,
                )
            )
            answer_relevance_results.append(
                await panel_judge(
                    llm_judge_answer_relevance,
                    case.question,
                    answer,
                    llm.chat,
                    panel_size=panel_size,
                )
            )

        summary["faithfulness"] = {
            "avg_score": _average_metric_score(faithfulness_results),
            "per_case": faithfulness_results,
        }
        summary["context_precision"] = {
            "avg_score": _average_metric_score(context_precision_results),
            "per_case": context_precision_results,
        }
        summary["answer_relevance"] = {
            "avg_score": _average_metric_score(answer_relevance_results),
            "per_case": answer_relevance_results,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = RESULTS_DIR / f"rag_eval_{timestamp}.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG evaluation.")
    parser.add_argument("--cases", default="eval/sample_questions.jsonl")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Enable LLM-as-judge metrics (answer_correctness, groundedness). Costs API calls.",
    )
    parser.add_argument(
        "--with-llm-judge",
        action="store_true",
        help="Enable LLM-as-judge metrics using the new flag name.",
    )
    parser.add_argument(
        "--panel-size",
        type=int,
        default=1,
        help="Run each LLM-as-judge metric N times and average (self-consistency panel).",
    )
    args = parser.parse_args()

    summary = await run_rag_evaluation(
        cases_path=args.cases,
        limit=args.limit,
        top_k=args.top_k,
        final_k=args.final_k,
        with_llm_judge=args.judge or args.with_llm_judge,
        panel_size=args.panel_size,
    )

    print(json.dumps(summary, indent=2, sort_keys=True))


def _average_metric_score(metrics: list[dict[str, Any]]) -> float:
    if not metrics:
        return 0.0
    return sum(float(item.get("score") or 0.0) for item in metrics) / len(metrics)


def _extract_result_text(result: object) -> str:
    if isinstance(result, dict):
        value = result.get("text", "")
    else:
        value = getattr(result, "text", "")
    return value if isinstance(value, str) else str(value)


if __name__ == "__main__":
    asyncio.run(main())

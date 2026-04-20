from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.services.evaluation_service import (
    compute_answer_correctness,
    compute_citation_usefulness,
    compute_groundedness,
    compute_retrieval_hit_rate,
    load_eval_cases,
)
from app.services.rag_service import RAGService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG evaluation (4 metrics).")
    parser.add_argument("--cases", default="eval/sample_questions.jsonl")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--final-k", type=int, default=5)
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Enable LLM-as-judge metrics (answer_correctness, groundedness). Costs API calls.",
    )
    args = parser.parse_args()

    cases = load_eval_cases(Path(args.cases))
    service = RAGService()

    search_batches: list[list[object]] = []
    answers: list[str] = []
    contexts: list[str] = []
    source_counts: list[int] = []

    for case in cases:
        search_result = await service.search(
            case.question, top_k=args.top_k, document_id=case.document_id,
        )
        search_batches.append(search_result["results"])

        ask_result = await service.ask(
            case.question,
            top_k=args.top_k,
            final_k=args.final_k,
            document_id=case.document_id,
        )
        answers.append(ask_result["answer"])
        contexts.append(RAGService.build_context(ask_result["sources"]))
        source_counts.append(len(ask_result["sources"]))

    summary: dict[str, object] = {
        "total_cases": len(cases),
        "top_k": args.top_k,
        "final_k": args.final_k,
        "retrieval_hit_rate": compute_retrieval_hit_rate(cases, search_batches),
        "citation": compute_citation_usefulness(answers, source_counts),
    }

    if args.judge:
        from app.services.llm_service import LLMService

        llm = LLMService()
        summary["answer_correctness"] = await compute_answer_correctness(
            cases, answers, llm.chat,
        )
        summary["groundedness"] = await compute_groundedness(
            answers, contexts, llm.chat,
        )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())

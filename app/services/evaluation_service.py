from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence


# Type alias: matches LLMService.chat() signature
JudgeFn = Callable[[str, str | None], Awaitable[dict[str, str]]]


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected_substring: str
    document_id: str | None = None
    reference_answer: str | None = None


def load_eval_cases(path: str | Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            cases.append(
                EvalCase(
                    question=row["question"],
                    expected_substring=row["expected_substring"],
                    document_id=row.get("document_id"),
                    reference_answer=row.get("reference_answer"),
                )
            )
    return cases


def compute_retrieval_hit_rate(
    cases: Sequence[EvalCase],
    result_batches: Sequence[Iterable[object]],
) -> float:
    if len(cases) != len(result_batches):
        raise ValueError("cases and result_batches must have the same length")
    if not cases:
        return 0.0

    hits = 0
    for case, results in zip(cases, result_batches):
        if any(case.expected_substring in _result_text(result) for result in results):
            hits += 1
    return hits / len(cases)


# ── Metric 2: Answer Correctness (LLM-as-judge) ──────────────────


async def judge_answer_correctness(
    question: str,
    answer: str,
    reference_answer: str,
    judge_fn: JudgeFn,
) -> bool:
    """LLM judges whether *answer* is semantically correct vs *reference_answer*."""
    from app.services.prompt_service import EVAL_CORRECTNESS_PROMPT

    prompt = EVAL_CORRECTNESS_PROMPT.format(
        question=question,
        reference_answer=reference_answer,
        candidate_answer=answer,
    )
    response = await judge_fn(prompt, None)
    return response["reply"].lower().strip().startswith("correct")


async def compute_answer_correctness(
    cases: Sequence[EvalCase],
    answers: Sequence[str],
    judge_fn: JudgeFn,
) -> float:
    """Fraction of answers judged correct (only cases with *reference_answer*)."""
    if len(cases) != len(answers):
        raise ValueError("cases and answers must have the same length")
    scorable = [(c, a) for c, a in zip(cases, answers) if c.reference_answer]
    if not scorable:
        return 0.0
    hits = 0
    for case, answer in scorable:
        if await judge_answer_correctness(
            case.question, answer, case.reference_answer, judge_fn
        ):
            hits += 1
    return hits / len(scorable)


# ── Metric 3: Groundedness (LLM-as-judge) ────────────────────────


async def judge_groundedness(
    answer: str,
    context: str,
    judge_fn: JudgeFn,
) -> bool:
    """LLM judges whether every claim in *answer* is supported by *context*."""
    from app.services.prompt_service import EVAL_GROUNDEDNESS_PROMPT

    prompt = EVAL_GROUNDEDNESS_PROMPT.format(context=context, answer=answer)
    response = await judge_fn(prompt, None)
    return response["reply"].lower().strip().startswith("grounded")


async def compute_groundedness(
    answers: Sequence[str],
    contexts: Sequence[str],
    judge_fn: JudgeFn,
) -> float:
    """Fraction of answers judged grounded in their context."""
    if len(answers) != len(contexts):
        raise ValueError("answers and contexts must have the same length")
    if not answers:
        return 0.0
    hits = 0
    for answer, context in zip(answers, contexts):
        if await judge_groundedness(answer, context, judge_fn):
            hits += 1
    return hits / len(answers)


# ── Metric 4: Citation / Source Usefulness ────────────────────────


def check_citation_usefulness(answer: str, num_sources: int) -> dict[str, object]:
    """Parse ``[n]`` citations from *answer* and measure coverage."""
    cited_indices: set[int] = set()
    for match in re.finditer(r"\[(\d+)\]", answer):
        cited_indices.add(int(match.group(1)))
    valid_cited = {i for i in cited_indices if 1 <= i <= num_sources}
    return {
        "has_citations": len(valid_cited) > 0,
        "cited_count": len(valid_cited),
        "total_sources": num_sources,
        "coverage": len(valid_cited) / num_sources if num_sources > 0 else 0.0,
        "invalid_citations": sorted(cited_indices - valid_cited),
    }


def compute_citation_usefulness(
    answers: Sequence[str],
    source_counts: Sequence[int],
) -> dict[str, float]:
    """Aggregate citation presence and coverage across all answers."""
    if len(answers) != len(source_counts):
        raise ValueError("answers and source_counts must have the same length")
    if not answers:
        return {"citation_presence": 0.0, "avg_coverage": 0.0}
    results = [check_citation_usefulness(a, n) for a, n in zip(answers, source_counts)]
    presence = sum(1 for r in results if r["has_citations"]) / len(results)
    avg_coverage = sum(r["coverage"] for r in results) / len(results)
    return {"citation_presence": presence, "avg_coverage": avg_coverage}


# ── Helpers ───────────────────────────────────────────────────────


def _result_text(result: object) -> str:
    value: Any
    if isinstance(result, dict):
        value = result.get("text", "")
    else:
        value = getattr(result, "text", "")
    return value if isinstance(value, str) else str(value)

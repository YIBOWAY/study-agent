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


async def llm_judge_faithfulness(
    question: str,
    answer: str,
    contexts: list[str],
    judge_fn: JudgeFn,
) -> dict[str, Any]:
    claim_prompt = (
        "Extract atomic factual claims from the answer. "
        "Return strict JSON: {\"claims\": [\"claim 1\", \"claim 2\"]}.\n\n"
        f"Question: {question}\nAnswer: {answer}"
    )
    claim_response = await judge_fn(claim_prompt, None)
    claim_payload = _safe_json_object(claim_response.get("reply", ""))
    raw_claims = claim_payload.get("claims")
    if not isinstance(raw_claims, list):
        return {"score": 0.0, "supported": 0, "total": 0, "claims": [], "reasoning": "parse_failed"}

    claims = [str(claim).strip() for claim in raw_claims if str(claim).strip()]
    if not claims:
        return {"score": 0.0, "supported": 0, "total": 0, "claims": [], "reasoning": "no_claims"}

    supported = 0
    checked_claims: list[dict[str, Any]] = []
    context_block = "\n\n".join(contexts)
    for claim in claims:
        support_prompt = (
            "Decide whether the context supports the claim. "
            "Return strict JSON: {\"supported\": true|false, \"reasoning\": \"...\"}.\n\n"
            f"Question: {question}\nClaim: {claim}\nContext:\n{context_block}"
        )
        support_response = await judge_fn(support_prompt, None)
        support_payload = _safe_json_object(support_response.get("reply", ""))
        is_supported = bool(support_payload.get("supported"))
        if is_supported:
            supported += 1
        checked_claims.append(
            {
                "claim": claim,
                "supported": is_supported,
                "reasoning": str(support_payload.get("reasoning") or ""),
            }
        )

    return {
        "score": supported / len(claims),
        "supported": supported,
        "total": len(claims),
        "claims": checked_claims,
    }


async def llm_judge_context_precision(
    question: str,
    contexts: list[str],
    judge_fn: JudgeFn,
) -> dict[str, Any]:
    if not contexts:
        return {"score": 0.0, "relevant": 0, "total": 0}

    relevant = 0
    for context in contexts:
        prompt = (
            "Decide whether the context is relevant to the question. "
            "Return strict JSON: {\"relevant\": true|false, \"reasoning\": \"...\"}.\n\n"
            f"Question: {question}\nContext:\n{context}"
        )
        response = await judge_fn(prompt, None)
        payload = _safe_json_object(response.get("reply", ""))
        if bool(payload.get("relevant")):
            relevant += 1

    return {"score": relevant / len(contexts), "relevant": relevant, "total": len(contexts)}


async def llm_judge_answer_relevance(
    question: str,
    answer: str,
    judge_fn: JudgeFn,
) -> dict[str, Any]:
    prompt = (
        "Rate whether the answer directly addresses the question on a 1-5 scale. "
        "Return strict JSON: {\"score\": 1, \"reasoning\": \"...\"}.\n\n"
        f"Question: {question}\nAnswer: {answer}"
    )
    response = await judge_fn(prompt, None)
    payload = _safe_json_object(response.get("reply", ""))
    try:
        raw_score = int(payload.get("score"))
    except (TypeError, ValueError):
        return {"score": 0.0, "raw_score": 0, "reasoning": "parse_failed"}
    raw_score = max(1, min(5, raw_score))
    return {
        "score": raw_score / 5,
        "raw_score": raw_score,
        "reasoning": str(payload.get("reasoning") or ""),
    }


def _safe_json_object(content: str) -> dict[str, Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


# ── Panel-of-judges (self-consistency) ────────────────────────────


async def panel_judge(
    judge_callable: Callable[..., Awaitable[dict[str, Any]]],
    *args: Any,
    panel_size: int = 3,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run a single-judge metric ``panel_size`` times and average the score.

    Useful for self-consistency when only one judge model is available: the same
    judge is invoked repeatedly. With a temperature-aware ``judge_fn`` you get
    real diversity; otherwise the runs are deterministic and ``stdev`` will be 0
    (still helpful as a sanity check / parsing-failure detector).
    """
    if panel_size < 1:
        raise ValueError("panel_size must be >= 1")

    runs: list[dict[str, Any]] = []
    for _ in range(panel_size):
        runs.append(await judge_callable(*args, **kwargs))

    scores = [float(run.get("score") or 0.0) for run in runs]
    mean = sum(scores) / len(scores)
    if len(scores) >= 2:
        variance = sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)
        stdev = variance**0.5
    else:
        stdev = 0.0

    aggregated = dict(runs[-1])
    aggregated["score"] = mean
    aggregated["panel"] = {
        "size": panel_size,
        "scores": scores,
        "stdev": stdev,
        "min": min(scores),
        "max": max(scores),
    }
    return aggregated

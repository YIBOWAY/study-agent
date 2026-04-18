import json

import pytest

from app.services.evaluation_service import (
    EvalCase,
    check_citation_usefulness,
    compute_answer_correctness,
    compute_citation_usefulness,
    compute_groundedness,
    compute_retrieval_hit_rate,
    judge_answer_correctness,
    judge_groundedness,
    load_eval_cases,
)


def test_load_eval_cases_reads_jsonl(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    rows = [
        {
            "question": "How did revenue change?",
            "expected_substring": "Revenue grew 20%",
            "document_id": "doc-1",
        },
        {
            "question": "Which page mentions the revenue increase?",
            "expected_substring": "page",
            "document_id": "doc-2",
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    cases = load_eval_cases(path)

    assert cases == [
        EvalCase(
            question="How did revenue change?",
            expected_substring="Revenue grew 20%",
            document_id="doc-1",
        ),
        EvalCase(
            question="Which page mentions the revenue increase?",
            expected_substring="page",
            document_id="doc-2",
        ),
    ]


def test_load_eval_cases_skips_blank_lines(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"question": "What is RAG?", "expected_substring": "retrieval", "document_id": "doc-1"}\n\n',
        encoding="utf-8",
    )

    assert load_eval_cases(path) == [
        EvalCase(question="What is RAG?", expected_substring="retrieval", document_id="doc-1")
    ]


def test_compute_retrieval_hit_rate_counts_cases_with_expected_substring_in_results() -> None:
    cases = [
        EvalCase(question="one", expected_substring="Revenue grew 20%"),
        EvalCase(question="two", expected_substring="page"),
        EvalCase(question="three", expected_substring="margin expansion"),
    ]
    result_batches = [
        [{"text": "Revenue grew 20% year over year."}],
        [{"text": "The answer appears on page 4 of the filing."}],
        [{"text": "Operating expenses declined."}],
    ]

    assert compute_retrieval_hit_rate(cases, result_batches) == pytest.approx(2 / 3)


def test_compute_retrieval_hit_rate_returns_zero_for_no_cases() -> None:
    assert compute_retrieval_hit_rate([], []) == 0.0


def test_compute_retrieval_hit_rate_rejects_mismatched_batches() -> None:
    cases = [EvalCase(question="one", expected_substring="Revenue")]

    with pytest.raises(ValueError, match="cases and result_batches must have the same length"):
        compute_retrieval_hit_rate(cases, [])


# ── load_eval_cases with reference_answer ─────────────────────────


def test_load_eval_cases_includes_reference_answer(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    row = {
        "question": "What is RAG?",
        "expected_substring": "retrieval",
        "reference_answer": "RAG is retrieval-augmented generation.",
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    cases = load_eval_cases(path)
    assert cases[0].reference_answer == "RAG is retrieval-augmented generation."


def test_load_eval_cases_reference_answer_defaults_to_none(tmp_path) -> None:
    path = tmp_path / "cases.jsonl"
    row = {"question": "Q", "expected_substring": "S"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    cases = load_eval_cases(path)
    assert cases[0].reference_answer is None


# ── Metric 2: Answer Correctness ─────────────────────────────────


@pytest.mark.asyncio
async def test_judge_answer_correctness_returns_true() -> None:
    async def fake_judge(prompt, system_prompt):
        return {"reply": "correct"}

    result = await judge_answer_correctness("q", "answer", "reference", fake_judge)
    assert result is True


@pytest.mark.asyncio
async def test_judge_answer_correctness_returns_false() -> None:
    async def fake_judge(prompt, system_prompt):
        return {"reply": "incorrect"}

    result = await judge_answer_correctness("q", "answer", "reference", fake_judge)
    assert result is False


@pytest.mark.asyncio
async def test_compute_answer_correctness_skips_cases_without_reference() -> None:
    cases = [
        EvalCase(question="q1", expected_substring="s", reference_answer="ref"),
        EvalCase(question="q2", expected_substring="s"),
    ]

    async def fake_judge(prompt, system_prompt):
        return {"reply": "correct"}

    result = await compute_answer_correctness(cases, ["a1", "a2"], fake_judge)
    assert result == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_compute_answer_correctness_returns_zero_when_no_scorable() -> None:
    cases = [EvalCase(question="q", expected_substring="s")]

    async def fake_judge(prompt, system_prompt):
        return {"reply": "correct"}

    assert await compute_answer_correctness(cases, ["a"], fake_judge) == 0.0


@pytest.mark.asyncio
async def test_compute_answer_correctness_rejects_mismatched() -> None:
    async def noop(p, s):
        return {"reply": ""}

    with pytest.raises(ValueError, match="cases and answers"):
        await compute_answer_correctness(
            [EvalCase(question="q", expected_substring="s")], [], noop
        )


# ── Metric 3: Groundedness ───────────────────────────────────────


@pytest.mark.asyncio
async def test_judge_groundedness_returns_true() -> None:
    async def fake_judge(prompt, system_prompt):
        return {"reply": "grounded"}

    result = await judge_groundedness("answer text", "context text", fake_judge)
    assert result is True


@pytest.mark.asyncio
async def test_judge_groundedness_returns_false() -> None:
    async def fake_judge(prompt, system_prompt):
        return {"reply": "ungrounded"}

    result = await judge_groundedness("answer text", "context text", fake_judge)
    assert result is False


@pytest.mark.asyncio
async def test_compute_groundedness_aggregate() -> None:
    call_count = 0

    async def fake_judge(prompt, system_prompt):
        nonlocal call_count
        call_count += 1
        return {"reply": "grounded" if call_count <= 2 else "ungrounded"}

    result = await compute_groundedness(
        ["a1", "a2", "a3"], ["c1", "c2", "c3"], fake_judge
    )
    assert result == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_compute_groundedness_empty() -> None:
    async def fake_judge(prompt, system_prompt):
        return {"reply": "grounded"}

    assert await compute_groundedness([], [], fake_judge) == 0.0


@pytest.mark.asyncio
async def test_compute_groundedness_rejects_mismatched() -> None:
    async def noop(p, s):
        return {"reply": ""}

    with pytest.raises(ValueError, match="answers and contexts"):
        await compute_groundedness(["a"], [], noop)


# ── Metric 4: Citation / Source Usefulness ────────────────────────


def test_check_citation_usefulness_with_valid_citations() -> None:
    result = check_citation_usefulness("Revenue grew [1] and costs fell [2].", 3)
    assert result["has_citations"] is True
    assert result["cited_count"] == 2
    assert result["total_sources"] == 3
    assert result["coverage"] == pytest.approx(2 / 3)
    assert result["invalid_citations"] == []


def test_check_citation_usefulness_with_invalid_citations() -> None:
    result = check_citation_usefulness("See [5] for details.", 3)
    assert result["has_citations"] is False
    assert result["cited_count"] == 0
    assert result["invalid_citations"] == [5]


def test_check_citation_usefulness_no_citations() -> None:
    result = check_citation_usefulness("No sources cited here.", 3)
    assert result["has_citations"] is False
    assert result["coverage"] == 0.0


def test_check_citation_usefulness_zero_sources() -> None:
    result = check_citation_usefulness("Some answer [1].", 0)
    assert result["coverage"] == 0.0
    assert result["invalid_citations"] == [1]


def test_compute_citation_usefulness_aggregate() -> None:
    answers = ["See [1] and [2].", "No citations.", "[1] only."]
    source_counts = [3, 2, 2]
    result = compute_citation_usefulness(answers, source_counts)
    assert result["citation_presence"] == pytest.approx(2 / 3)
    assert result["avg_coverage"] == pytest.approx((2 / 3 + 0 + 1 / 2) / 3)


def test_compute_citation_usefulness_empty() -> None:
    result = compute_citation_usefulness([], [])
    assert result == {"citation_presence": 0.0, "avg_coverage": 0.0}


def test_compute_citation_usefulness_rejects_mismatched() -> None:
    with pytest.raises(ValueError, match="answers and source_counts"):
        compute_citation_usefulness(["a"], [])

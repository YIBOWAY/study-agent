from __future__ import annotations

from app.services.cost_calculator import calculate_cost


def test_calculate_cost_known_model() -> None:
    result = calculate_cost("gpt-5.4", prompt_tokens=1_000, completion_tokens=500)

    assert result == 0.0125


def test_calculate_cost_unknown_model_returns_zero() -> None:
    result = calculate_cost("unknown-model", prompt_tokens=1_000, completion_tokens=500)

    assert result == 0.0

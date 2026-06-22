from __future__ import annotations

# Pricing in USD per 1M tokens. Update from each vendor's official pricing page
# whenever the model changes. Aliases (lowercase) covered for common API gateway names.
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-5.4": {"input": 5.0, "output": 15.0},  # placeholder for project gateway
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    # Embeddings (output cost is 0)
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = DEFAULT_PRICING.get(model) or DEFAULT_PRICING.get(model.lower())
    if pricing is None:
        return 0.0
    return (
        prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]
    ) / 1_000_000

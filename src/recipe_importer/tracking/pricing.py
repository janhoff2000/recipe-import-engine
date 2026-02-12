"""Model pricing table for cost estimation."""

# (input_per_1m_tokens, output_per_1m_tokens) in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-5-nano": (0.10, 0.40),  # placeholder
    "gpt-5-mini": (1.00, 4.00),  # placeholder
    "gemini-2.5-flash-lite": (0.00, 0.00),  # placeholder
    "apple-intelligence": (0.00, 0.00),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Estimate extraction cost in USD based on token usage."""
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return None
    input_rate, output_rate = pricing
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000

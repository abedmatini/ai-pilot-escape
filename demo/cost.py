"""Rough cost telemetry for the projector — not an invoice.

Gemini 3.6 Flash introductory global prices checked in September 2026:
  $0.75 / 1M input tokens, $3.75 / 1M output tokens.
Local Ollama is treated as $0.00 API spend; evaluate its operating cost
separately before claiming production savings.
"""

from __future__ import annotations

CLOUD_INPUT_USD_PER_M = 0.75
CLOUD_OUTPUT_USD_PER_M = 3.75


def estimate_tokens(text: str) -> int:
    """Cheap stand-in when the provider does not return usage."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost_usd(
    *,
    route_model: str,
    prompt: str,
    completion: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> float:
    if route_model == "local" or route_model.startswith("ollama"):
        return 0.0
    pin = prompt_tokens if prompt_tokens is not None else estimate_tokens(prompt)
    pout = completion_tokens if completion_tokens is not None else estimate_tokens(completion)
    return (pin / 1_000_000.0) * CLOUD_INPUT_USD_PER_M + (
        pout / 1_000_000.0
    ) * CLOUD_OUTPUT_USD_PER_M

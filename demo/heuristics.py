"""Transparent routing heuristics for the live demo.

This is *not* RouteLLM or a semantic router. It is the explainable stand-in:
word count, intent keywords, and (elsewhere) PII regex. Good enough to teach
the policy; replace with a learned router once you have traces.
"""

from __future__ import annotations

from dataclasses import dataclass

HARD_KEYWORDS = (
    "architecture",
    "architect",
    "multi-step",
    "multi step",
    "trade-off",
    "tradeoff",
    "trade offs",
    "design a system",
    "design an architecture",
    "reason about",
    "reason through",
    "compare and contrast",
    "threat model",
    "distributed",
    "consensus",
    "evaluate alternatives",
    "step by step",
    "step-by-step",
    "blueprint",
    "production-ready",
    "production ready",
    "scale this",
    "failure modes",
    "prove that",
    "derive",
)

EASY_KEYWORDS = (
    "summarize",
    "summary",
    "tl;dr",
    "tldr",
    "classify",
    "categorize",
    "extract json",
    "as json",
    "json only",
    "sentiment",
    "rewrite briefly",
    "one sentence",
    "one-liner",
    "bullet points",
    "bullets",
    "shorten",
    "eli5",
    "plain english",
)

# Scenario D / quality-fallback: local 0.5B answers that skip the assignment.
WEAK_MARKERS = (
    "i don't know",
    "i do not know",
    "cannot help",
    "as an ai",
    "i'm not sure",
    "i am not sure",
    "sorry, i",
)


@dataclass(frozen=True)
class Classification:
    difficulty: str  # "easy" | "hard"
    reason: str
    word_count: int
    easy_hits: tuple[str, ...]
    hard_hits: tuple[str, ...]


def word_count(text: str) -> int:
    return len(text.split())


def _hits(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(k for k in keywords if k in lower)


def classify(text: str) -> Classification:
    """Return easy vs hard plus a one-line reason suitable for a projector."""
    words = word_count(text)
    easy = _hits(text, EASY_KEYWORDS)
    hard = _hits(text, HARD_KEYWORDS)

    if hard:
        return Classification(
            difficulty="hard",
            reason=f"hard keywords ({', '.join(hard[:3])}) — reserve cloud reasoning",
            word_count=words,
            easy_hits=easy,
            hard_hits=hard,
        )

    if words >= 120:
        return Classification(
            difficulty="hard",
            reason=f"long prompt ({words} words) — treat as heavy reasoning",
            word_count=words,
            easy_hits=easy,
            hard_hits=hard,
        )

    if easy and words <= 80:
        return Classification(
            difficulty="easy",
            reason=f"short {easy[0]} ({words} words) — local SLM is enough",
            word_count=words,
            easy_hits=easy,
            hard_hits=hard,
        )

    if words <= 40:
        return Classification(
            difficulty="easy",
            reason=f"short prompt ({words} words), no hard markers — local",
            word_count=words,
            easy_hits=easy,
            hard_hits=hard,
        )

    return Classification(
        difficulty="hard",
        reason=f"ambiguous mid-size prompt ({words} words) — default to cloud quality",
        word_count=words,
        easy_hits=easy,
        hard_hits=hard,
    )


def looks_weak(response: str, *, hard: bool) -> bool:
    """Stage-safe quality check after a forced-local call on a hard prompt."""
    text = (response or "").strip()
    if not text:
        return True
    lower = text.lower()
    if any(marker in lower for marker in WEAK_MARKERS):
        return True
    if hard and len(text) < 80:
        return True
    if hard:
        structure = ("1.", "1)", "- ", "* ", "trade", "component", "layer")
        if not any(token in lower for token in structure):
            return True
    return False

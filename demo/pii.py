"""Edge pre-processing: regex PII detection and redaction.

Regex is enough for the live demo. An optional local-SLM pass can sit on top
(`--slm-redact`) but must not be required for the talk to succeed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Named so the audience can see *what* left the prompt, not the raw secret.
_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", re.IGNORECASE)),
    (
        "PHONE",
        # Require a +country or a formatted local number so raw order IDs stay put.
        re.compile(
            r"(?<!\w)(?:\+\d{1,3}[\s-]\d{2,4}[\s-]\d{3,4}[\s-]?\d{3,4}|0\d{2}[\s-]\d{3}[\s-]\d{4})(?!\w)"
        ),
    ),
    ("SA_ID", re.compile(r"\b\d{13}\b")),
    (
        "ACCOUNT",
        re.compile(
            r"\b(?:account|acct|acc(?:ount)?\s*(?:no|number|#))[:\s#-]*(\d{6,12})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "API_KEY",
        re.compile(
            r"\b(?:AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})\b"
        ),
    ),
    (
        "CC",
        re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    ),
)


@dataclass
class Redaction:
    original: str
    redacted: str
    found: list[str] = field(default_factory=list)
    replacements: dict[str, str] = field(default_factory=dict)

    @property
    def has_pii(self) -> bool:
        return bool(self.found)


def _looks_like_card(number: str) -> bool:
    digits = re.sub(r"\D", "", number)
    if len(digits) < 13 or len(digits) > 19:
        return False
    # Luhn — avoid redacting random long integers (order ids, etc.).
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def redact(text: str) -> Redaction:
    """Replace detected PII with stable placeholders like [EMAIL_1]."""
    hits: list[tuple[int, int, str, str]] = []
    for label, pattern in _RULES:
        for match in pattern.finditer(text):
            raw = match.group(0)
            start, end = match.start(), match.end()
            if label == "CC" and not _looks_like_card(raw):
                continue
            if label == "ACCOUNT":
                if not match.lastindex:
                    continue
                raw = match.group(1)
                start, end = match.start(1), match.end(1)
            if label == "PHONE":
                digits = re.sub(r"\D", "", raw)
                if len(digits) < 9:
                    continue
            hits.append((start, end, label, raw))

    hits.sort(key=lambda h: h[0])
    # Drop overlaps — keep the earlier (and therefore already-sorted) span.
    kept: list[tuple[int, int, str, str]] = []
    last_end = -1
    for start, end, label, raw in hits:
        if start < last_end:
            continue
        kept.append((start, end, label, raw))
        last_end = end

    found: list[str] = []
    replacements: dict[str, str] = {}
    counters: dict[str, int] = {}
    seen_raw: dict[str, str] = {}
    labeled: list[tuple[int, int, str]] = []
    for start, end, label, raw in kept:
        token = seen_raw.get(raw)
        if token is None:
            counters[label] = counters.get(label, 0) + 1
            token = f"[{label}_{counters[label]}]"
            seen_raw[raw] = token
            replacements[token] = raw
            found.append(f"{label}:{raw}")
        labeled.append((start, end, token))

    result = text
    for start, end, token in reversed(labeled):
        result = result[:start] + token + result[end:]

    return Redaction(original=text, redacted=result, found=found, replacements=replacements)

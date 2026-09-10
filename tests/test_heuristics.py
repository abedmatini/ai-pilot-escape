from pathlib import Path

from demo.heuristics import classify, looks_weak
from demo.router import pick_route, read_prompt

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> str:
    class Args:
        prompt = None
        prompt_file = None
        scenario = name

    return read_prompt(Args())


def test_scenario_a_is_easy_local():
    text = _load("A")
    c = classify(text)
    assert c.difficulty == "easy"
    alias, reason, _, _ = pick_route(
        text, force_local=False, force_cloud=False, cloud_after_redact=False
    )
    assert alias == "local"
    assert "local" in reason.lower() or "summar" in reason.lower()


def test_scenario_b_is_hard_cloud():
    text = _load("B")
    c = classify(text)
    assert c.difficulty == "hard"
    alias, reason, _, redaction = pick_route(
        text, force_local=False, force_cloud=False, cloud_after_redact=False
    )
    assert alias == "cloud"
    assert not redaction.has_pii
    assert "hard" in reason.lower() or "architecture" in reason.lower()


def test_scenario_c_redacts_then_cloud():
    text = _load("C")
    alias, reason, _, redaction = pick_route(
        text, force_local=False, force_cloud=False, cloud_after_redact=True
    )
    assert redaction.has_pii
    assert alias == "cloud"
    assert "PII" in reason
    joined = " ".join(redaction.found)
    assert "EMAIL" in joined
    assert "PHONE" in joined
    assert "SA_ID" in joined or "ACCOUNT" in joined
    assert "priya.naidoo@example.net" not in redaction.redacted
    assert "9001014800088" not in redaction.redacted
    assert "[EMAIL_" in redaction.redacted


def test_scenario_d_force_local_on_hard():
    text = _load("D")
    assert classify(text).difficulty == "hard"
    alias, reason, _, _ = pick_route(
        text, force_local=True, force_cloud=False, cloud_after_redact=False
    )
    assert alias == "local"
    assert "forced local" in reason


def test_looks_weak_on_thin_hard_answer():
    assert looks_weak("Okay.", hard=True)
    assert looks_weak("I don't know how to do that.", hard=True)
    assert not looks_weak(
        "1. Split easy vs hard prompts.\n2. Put a gateway in front.\n"
        "Trade-offs: cost vs quality. Components sit at the edge layer.",
        hard=True,
    )

#!/usr/bin/env python3
"""Heuristic hybrid router — the live-demo `auto` path.

Prints route / reason / model / latency_ms / est_cost_usd on every call.
Falls back to cloud once if the local path errors (or looks weak on a hard task).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from demo.client import complete
from demo.heuristics import classify
from demo.pii import redact

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "demo" / "prompts"

SCENARIO_FILES = {
    "A": PROMPTS / "A_easy.md",
    "B": PROMPTS / "B_hard.md",
    "C": PROMPTS / "C_pii.md",
    "D": PROMPTS / "D_force_local.md",
}

SLM_REDACT_INSTRUCTION = (
    "Rewrite the user text. Replace every email, phone number, national id, "
    "account number, API key, and card number with placeholders like [EMAIL_1]. "
    "Keep the rest of the wording. Return only the rewritten text."
)


@dataclass
class Telemetry:
    route: str
    reason: str
    model: str
    latency_ms: int
    est_cost_usd: float
    fallback: bool = False
    pii_redacted: bool = False
    pii_found: list[str] = field(default_factory=list)
    difficulty: str = ""
    word_count: int = 0


def load_env() -> None:
    load_dotenv(ROOT / ".env")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt.strip()
    path: Path | None = None
    if args.prompt_file:
        path = Path(args.prompt_file)
    elif args.scenario:
        path = SCENARIO_FILES[args.scenario]
    if path is None:
        raise SystemExit("Provide --scenario A|B|C|D, --prompt, or --prompt-file.")
    if not path.exists():
        raise SystemExit(f"Prompt file not found: {path}")
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def pick_route(
    text: str,
    *,
    force_local: bool,
    force_cloud: bool,
    cloud_after_redact: bool,
) -> tuple[str, str, object, object]:
    """Return (alias, reason, classification, redaction). alias is local|cloud."""
    classification = classify(text)
    redaction = redact(text)

    if force_local:
        return (
            "local",
            "forced local (--force-local or scenario D)",
            classification,
            redaction,
        )
    if force_cloud:
        return "cloud", "forced cloud (--force-cloud)", classification, redaction

    if redaction.has_pii:
        if cloud_after_redact or classification.difficulty == "hard":
            return (
                "cloud",
                f"PII detected ({len(redaction.found)} spans) — redact locally, then cloud on clean text",
                classification,
                redaction,
            )
        return (
            "local",
            f"PII detected ({len(redaction.found)} spans) — redact locally, keep easy task on local",
            classification,
            redaction,
        )

    if classification.difficulty == "easy":
        return "local", classification.reason, classification, redaction
    return "cloud", classification.reason, classification, redaction


def slm_redact(text: str, *, via_proxy: bool, timeout: float) -> str:
    result = complete(
        "local",
        [
            {"role": "system", "content": SLM_REDACT_INSTRUCTION},
            {"role": "user", "content": text},
        ],
        via_proxy=via_proxy,
        timeout=timeout,
    )
    return result.text.strip() or text


def call_alias(alias: str, user_text: str, *, via_proxy: bool, timeout: float):
    return complete(
        alias,
        [{"role": "user", "content": user_text}],
        via_proxy=via_proxy,
        timeout=timeout,
    )


def print_telemetry(tel: Telemetry, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(tel), indent=2))
        return
    width = 56
    print("─" * width)
    rows = [
        ("route", tel.route),
        ("reason", tel.reason),
        ("model", tel.model),
        ("latency_ms", str(tel.latency_ms)),
        ("est_cost_usd", f"{tel.est_cost_usd:.6f}"),
        ("fallback", str(tel.fallback).lower()),
        ("pii_redacted", str(tel.pii_redacted).lower()),
        ("difficulty", tel.difficulty),
    ]
    for key, value in rows:
        print(f" {key:<16} {value}")
    print("─" * width)


def run(args: argparse.Namespace) -> int:
    from demo.turn import TurnRequest, execute_turn

    load_env()
    prompt = read_prompt(args)
    force_local = args.force_local or args.scenario == "D"
    force_cloud = args.force_cloud
    cloud_after_redact = args.cloud_after_redact
    if args.scenario == "C" and not args.no_cloud_after_redact:
        cloud_after_redact = True

    outcome = execute_turn(
        TurnRequest(
            prompt=prompt,
            force_local=force_local,
            force_cloud=force_cloud,
            cloud_after_redact=cloud_after_redact,
            dry_run=args.dry_run,
            via_proxy=args.via_proxy,
            timeout=args.timeout,
            slm_redact=args.slm_redact,
            keep_pii=args.keep_pii,
            no_quality_fallback=args.no_quality_fallback,
        )
    )

    if not args.json:
        print("\n▸ user prompt")
        print(prompt)
        if outcome.telemetry.pii_redacted:
            print("\n▸ after local redaction (this is what may leave the machine)")
            print(outcome.outgoing)
        if outcome.local_preview:
            print("\n▸ local completion (expected to be thin on a 0.5B model)")
            print(outcome.local_preview)
            print("▸ quality fallback → cloud")

    if not outcome.ok:
        print(outcome.error or "turn failed", file=sys.stderr)
        return outcome.exit_code

    if args.dry_run:
        print_telemetry(outcome.telemetry, as_json=args.json)
        return 0

    if not args.json:
        print("\n▸ completion")
        print(outcome.completion)
        print()
    print_telemetry(outcome.telemetry, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Heuristic hybrid router (aliases: local, cloud, auto).",
    )
    p.add_argument("--scenario", choices=sorted(SCENARIO_FILES), help="Seed prompt A–D")
    p.add_argument("--prompt", help="Inline user prompt")
    p.add_argument("--prompt-file", help="Path to a prompt file")
    p.add_argument("--force-local", action="store_true", help="Pin the first hop to local")
    p.add_argument("--force-cloud", action="store_true", help="Pin the first hop to cloud")
    p.add_argument("--via-proxy", action="store_true", help="Call LiteLLM aliases local|cloud")
    p.add_argument("--dry-run", action="store_true", help="Classify only — no model calls")
    p.add_argument("--json", action="store_true", help="Telemetry as JSON")
    p.add_argument("--no-quality-fallback", action="store_true")
    p.add_argument("--slm-redact", action="store_true", help="Optional local-model PII pass")
    p.add_argument(
        "--cloud-after-redact",
        action="store_true",
        help="After regex redaction, send the clean text to cloud",
    )
    p.add_argument("--no-cloud-after-redact", action="store_true")
    p.add_argument("--keep-pii", action="store_true", help="Do not redact (debug only)")
    p.add_argument("--timeout", type=float, default=90.0, help="Per-call timeout seconds")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.force_local and args.force_cloud:
        print("Choose only one of --force-local / --force-cloud", file=sys.stderr)
        return 2
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())

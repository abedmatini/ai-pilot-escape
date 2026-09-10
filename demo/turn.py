"""One routed generation — shared by the CLI and the chat API."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from demo.client import DEFAULT_CLOUD_MODEL
from demo.cost import estimate_cost_usd
from demo.heuristics import looks_weak
from demo.router import call_alias, pick_route, slm_redact
from demo.router import Telemetry


@dataclass
class TurnRequest:
    prompt: str
    force_local: bool = False
    force_cloud: bool = False
    cloud_after_redact: bool = False
    dry_run: bool = False
    via_proxy: bool = False
    timeout: float = 90.0
    slm_redact: bool = False
    keep_pii: bool = False
    no_quality_fallback: bool = False


@dataclass
class TurnOutcome:
    ok: bool
    completion: str
    outgoing: str
    telemetry: Telemetry
    scenario: str
    scenario_label: str
    local_preview: str | None = None
    error: str | None = None
    exit_code: int = 0
    pii_found: list[str] = field(default_factory=list)


SCENARIO_NOTES = {
    "A": "Easy → local",
    "B": "Hard → cloud",
    "C": "PII → redact → cloud",
    "D": "Force local → fallback",
}


def label_scenario(*, force_local: bool, has_pii: bool, difficulty: str) -> tuple[str, str]:
    if force_local:
        return "D", SCENARIO_NOTES["D"]
    if has_pii:
        return "C", SCENARIO_NOTES["C"]
    if difficulty == "easy":
        return "A", SCENARIO_NOTES["A"]
    return "B", SCENARIO_NOTES["B"]


def execute_turn(req: TurnRequest) -> TurnOutcome:
    prompt = req.prompt.strip()
    alias, reason, classification, redaction = pick_route(
        prompt,
        force_local=req.force_local,
        force_cloud=req.force_cloud,
        cloud_after_redact=req.cloud_after_redact,
    )
    scenario, scenario_label = label_scenario(
        force_local=req.force_local,
        has_pii=redaction.has_pii,
        difficulty=classification.difficulty,
    )

    outgoing = prompt
    if redaction.has_pii and not req.keep_pii:
        outgoing = redaction.redacted
        if req.slm_redact and not req.dry_run:
            outgoing = slm_redact(outgoing, via_proxy=req.via_proxy, timeout=req.timeout)

    def _tel(
        *,
        route: str,
        model: str,
        latency_ms: int,
        cost: float,
        fallback: bool,
        reason_text: str,
    ) -> Telemetry:
        return Telemetry(
            route=route,
            reason=reason_text,
            model=model,
            latency_ms=latency_ms,
            est_cost_usd=cost,
            fallback=fallback,
            pii_redacted=redaction.has_pii and outgoing != prompt,
            pii_found=redaction.found,
            difficulty=classification.difficulty,
            word_count=classification.word_count,
        )

    def _out(
        *,
        ok: bool,
        telemetry: Telemetry,
        completion: str = "",
        local_preview: str | None = None,
        error: str | None = None,
        exit_code: int = 0,
    ) -> TurnOutcome:
        return TurnOutcome(
            ok=ok,
            completion=completion,
            outgoing=outgoing,
            telemetry=telemetry,
            scenario=scenario,
            scenario_label=scenario_label,
            local_preview=local_preview,
            error=error,
            exit_code=exit_code,
            pii_found=list(redaction.found),
        )

    if req.dry_run:
        return _out(
            ok=True,
            completion="",
            telemetry=_tel(
                route="auto/" + alias,
                model="local" if alias == "local" else "cloud",
                latency_ms=0,
                cost=0.0,
                fallback=False,
                reason_text=reason + " [dry-run: no model call]",
            ),
        )

    if alias == "cloud" and not os.getenv("GEMINI_API_KEY") and not req.via_proxy:
        return _out(
            ok=False,
            error=(
                "GEMINI_API_KEY is empty. Copy .env.example → .env and paste a "
                "Google AI Studio key."
            ),
            exit_code=2,
            telemetry=_tel(
                route="auto/cloud",
                model=os.getenv("CLOUD_MODEL", DEFAULT_CLOUD_MODEL),
                latency_ms=0,
                cost=0.0,
                fallback=False,
                reason_text=reason,
            ),
        )

    started = time.perf_counter()
    fallback = False
    used_alias = alias
    transport_error: Exception | None = None
    result = None
    local_preview: str | None = None

    try:
        result = call_alias(alias, outgoing, via_proxy=req.via_proxy, timeout=req.timeout)
    except Exception as exc:  # noqa: BLE001
        transport_error = exc
        if alias != "local":
            return _out(
                ok=False,
                error=f"cloud call failed: {exc}",
                exit_code=1,
                telemetry=_tel(
                    route="auto/cloud",
                    model=os.getenv("CLOUD_MODEL", DEFAULT_CLOUD_MODEL),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    cost=0.0,
                    fallback=False,
                    reason_text=reason,
                ),
            )
        fallback = True
        used_alias = "cloud"
        try:
            result = call_alias("cloud", outgoing, via_proxy=req.via_proxy, timeout=req.timeout)
        except Exception as cloud_exc:  # noqa: BLE001
            return _out(
                ok=False,
                error=f"cloud fallback also failed: {cloud_exc}",
                exit_code=1,
                telemetry=_tel(
                    route="auto/cloud",
                    model=os.getenv("CLOUD_MODEL", DEFAULT_CLOUD_MODEL),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    cost=0.0,
                    fallback=True,
                    reason_text=f"{reason} — fallback failed",
                ),
            )

    quality_fallback = (
        result is not None
        and alias == "local"
        and not fallback
        and not req.no_quality_fallback
        and (req.force_local or classification.difficulty == "hard")
        and looks_weak(result.text, hard=True)
    )
    if quality_fallback:
        local_preview = result.text.strip() or "(empty)"
        local_result = result
        try:
            result = call_alias("cloud", outgoing, via_proxy=req.via_proxy, timeout=req.timeout)
            fallback = True
            used_alias = "cloud"
            reason = "force-local on hard task produced a weak answer — fallback cloud"
        except Exception:  # noqa: BLE001
            result = local_result
            local_preview = None

    latency_ms = int((time.perf_counter() - started) * 1000)
    assert result is not None
    cost = estimate_cost_usd(
        route_model=used_alias,
        prompt=outgoing,
        completion=result.text,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
    )
    display_model = result.model
    if used_alias == "local" and "gemini" not in display_model.lower():
        display_model = os.getenv("LOCAL_MODEL", "ollama/qwen2.5:0.5b")
    elif used_alias == "cloud":
        display_model = os.getenv("CLOUD_MODEL", DEFAULT_CLOUD_MODEL)

    if fallback:
        route_label = "auto/cloud"
        if "fallback" not in reason.lower():
            err_name = transport_error.__class__.__name__ if transport_error else "quality"
            reason = f"{reason} — fallback=true ({err_name})"
    else:
        route_label = f"auto/{used_alias}"

    return _out(
        ok=True,
        completion=result.text.strip() or "(empty)",
        local_preview=local_preview,
        telemetry=_tel(
            route=route_label,
            model=display_model,
            latency_ms=latency_ms,
            cost=cost,
            fallback=fallback,
            reason_text=reason,
        ),
    )

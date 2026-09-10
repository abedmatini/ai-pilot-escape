"""Model calls: LiteLLM Python SDK (default) or the LiteLLM proxy aliases."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

DEFAULT_CLOUD_MODEL = "gemini/gemini-3.6-flash"


@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def resolve_model(alias: str) -> str:
    if alias == "local":
        return os.getenv("LOCAL_MODEL", "ollama/qwen2.5:0.5b")
    if alias == "cloud":
        return os.getenv("CLOUD_MODEL", DEFAULT_CLOUD_MODEL)
    raise ValueError(f"unknown alias: {alias}")


def complete_via_sdk(alias: str, messages: list[dict[str, str]], timeout: float) -> CompletionResult:
    import litellm

    model = resolve_model(alias)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout,
    }
    if alias == "local":
        kwargs["api_base"] = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    response = litellm.completion(**kwargs)
    text = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    return CompletionResult(
        text=text,
        model=getattr(response, "model", None) or model,
        prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
    )


def complete_via_proxy(alias: str, messages: list[dict[str, str]], timeout: float) -> CompletionResult:
    import httpx

    base = os.getenv("LITELLM_BASE_URL", "http://127.0.0.1:4000").rstrip("/")
    headers = {"Content-Type": "application/json"}
    master = os.getenv("LITELLM_MASTER_KEY")
    if master:
        headers["Authorization"] = f"Bearer {master}"
    payload = {"model": alias, "messages": messages}
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{base}/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    text = data["choices"][0]["message"].get("content") or ""
    usage = data.get("usage") or {}
    return CompletionResult(
        text=text,
        model=data.get("model") or alias,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )


def complete(
    alias: str,
    messages: list[dict[str, str]],
    *,
    via_proxy: bool,
    timeout: float,
) -> CompletionResult:
    if via_proxy:
        return complete_via_proxy(alias, messages, timeout)
    return complete_via_sdk(alias, messages, timeout)

"""FastAPI app: same router as the CLI, plus a small chat page."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from demo.router import ROOT, load_env, read_prompt
from demo.turn import SCENARIO_NOTES, TurnRequest, execute_turn

load_env()

WEB_DIST = ROOT / "web" / "dist"

app = FastAPI(title="Hybrid router chat", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    prompt: str = Field(min_length=1)
    force_local: bool = False
    dry_run: bool = False


class SeedOut(BaseModel):
    id: str
    label: str
    note: str
    force_local: bool
    prompt: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/seeds")
def seeds() -> list[SeedOut]:
    rows: list[SeedOut] = []
    for sid, note in SCENARIO_NOTES.items():

        class Args:
            prompt = None
            prompt_file = None
            scenario = sid

        rows.append(
            SeedOut(
                id=sid,
                label=f"Scenario {sid}",
                note=note,
                force_local=sid == "D",
                prompt=read_prompt(Args()),
            )
        )
    return rows


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    prompt = body.prompt.strip()
    if not prompt:
        return {"ok": False, "error": "Type something first.", "exit_code": 2}

    outcome = execute_turn(
        TurnRequest(
            prompt=prompt,
            force_local=body.force_local,
            cloud_after_redact=True,
            dry_run=body.dry_run,
        )
    )
    return {
        "ok": outcome.ok,
        "error": outcome.error,
        "exit_code": outcome.exit_code,
        "completion": outcome.completion,
        "outgoing": outcome.outgoing,
        "local_preview": outcome.local_preview,
        "scenario": outcome.scenario,
        "scenario_label": outcome.scenario_label,
        "pii_found": outcome.pii_found,
        "telemetry": asdict(outcome.telemetry),
    }


if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str) -> FileResponse:
        file = WEB_DIST / path
        if path and file.is_file():
            return FileResponse(file)
        return FileResponse(WEB_DIST / "index.html")

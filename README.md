# Hybrid local-to-cloud AI demo

Route predictable AI workloads to a local model and reserve a cloud model for tasks that need more capability.

This repository is the runnable demo from **Stop Paying for Easy Prompts: Architecting Hybrid Local-to-Cloud AI Systems**.

## What it demonstrates

- Explainable per-request routing between local and cloud models
- Local inference through Ollama using `qwen2.5:0.5b`
- Cloud inference through Google Gemini and LiteLLM
- Local PII redaction before a cloud request
- One controlled cloud fallback when a local result fails
- Route, reason, model, latency, fallback, and estimated-cost telemetry
- A small chat UI and four repeatable CLI scenarios

The routing policy is intentionally simple and inspectable. It is a demonstration of the architecture, not a production routing benchmark.

## Repository contents

```text
demo/                    Router, heuristics, redaction, cost, and prompts
chat/                    FastAPI chat API using the same router
web/                     Vite and React chat interface
tests/                   Unit and API tests
scripts/                 Setup and run helpers
docs/peer-local.md        Optional governed worker-pool extension
.env.example             Environment template without secrets
```

## Requirements

- Python 3.11+
- Ollama
- Node.js 18+ when using the web interface
- A Gemini API key for cloud requests

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your key to `.env`:

```dotenv
GEMINI_API_KEY=your_key_here
```

Never commit `.env`.

Install Ollama, then download and warm the demonstration model:

```bash
./scripts/warm-ollama.sh
```

## Run the CLI scenarios

```bash
python -m demo.router --scenario A   # easy → local
python -m demo.router --scenario B   # hard → cloud
python -m demo.router --scenario C   # PII → redact locally → cloud
python -m demo.router --scenario D   # forced local → controlled fallback
```

Run all four:

```bash
./scripts/run-demos.sh
```

Inspect routing decisions without calling either model:

```bash
./scripts/run-demos.sh --dry-run
```

## Run the chat interface

```bash
./scripts/start-chat.sh
```

Open [http://127.0.0.1:43173](http://127.0.0.1:43173).

For frontend hot reload:

```bash
# terminal 1
.venv/bin/python -m uvicorn chat.server:app --host 127.0.0.1 --port 43173

# terminal 2
npm --prefix web install
npm --prefix web run dev
```

Open [http://127.0.0.1:43174](http://127.0.0.1:43174).

## Optional LiteLLM proxy

```bash
./scripts/start-litellm.sh

# in another terminal
python -m demo.router --scenario A --via-proxy
```

The proxy aliases are:

- `local` → Ollama
- `cloud` → Gemini

The application policy owns `auto`; it is not another provider model.

## Tests

Tests do not require an API key:

```bash
source .venv/bin/activate
pytest
```

## Important boundaries

- A short prompt is not automatically easy. Task capability, sensitivity, ambiguity, output contract, and risk matter.
- A model result is a candidate until it passes the required validation.
- Redaction reduces exposure; it does not guarantee privacy or regulatory compliance.
- Local inference avoids cloud API charges but still has hardware and operating costs.
- The demo uses simple heuristics and fallback checks. Production thresholds should come from labelled traces and task evaluations.

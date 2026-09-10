#!/usr/bin/env bash
# Start the LiteLLM proxy with aliases `local` and `cloud`.
# `auto` is the heuristic CLI (python -m demo.router), not a third vendor model.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
else
  echo "No .env file. Copy .env.example → .env and paste GEMINI_API_KEY."
  echo "Cloud alias will fail until you do. Local alias can still work."
fi

if [[ -x "${ROOT}/.venv/bin/litellm" ]]; then
  LITELLM="${ROOT}/.venv/bin/litellm"
elif command -v litellm >/dev/null 2>&1; then
  LITELLM="litellm"
else
  echo "LiteLLM not found. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

PORT="${LITELLM_PORT:-4000}"
HOST="${LITELLM_HOST:-127.0.0.1}"

echo "▸ LiteLLM proxy  http://${HOST}:${PORT}"
echo "▸ aliases        local → ollama/qwen2.5:0.5b"
echo "▸                cloud → ${CLOUD_MODEL:-gemini/gemini-3.6-flash}"
echo "▸ auto           python -m demo.router   (not a proxy model name)"

exec "${LITELLM}" --config "${ROOT}/demo/litellm_config.yaml" --host "${HOST}" --port "${PORT}"

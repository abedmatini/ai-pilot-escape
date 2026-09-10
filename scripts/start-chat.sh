#!/usr/bin/env bash
# Chat UI for the hybrid router. Builds the Vite app if needed, then serves
# API + UI on http://127.0.0.1:43173
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
else
  PY="python3"
fi

if [[ ! -d "${ROOT}/web/node_modules" ]]; then
  echo "▸ npm install in web/"
  npm --prefix "${ROOT}/web" install
fi

if [[ ! -d "${ROOT}/web/dist" ]]; then
  echo "▸ building chat UI"
  npm --prefix "${ROOT}/web" run build
fi

HOST="${CHAT_HOST:-127.0.0.1}"
PORT="${CHAT_PORT:-43173}"
echo "▸ chat  http://${HOST}:${PORT}"
echo "▸ API   POST /api/chat   GET /api/seeds"
exec "${PY}" -m uvicorn chat.server:app --host "${HOST}" --port "${PORT}"

#!/usr/bin/env bash
# Pull and warm the single v1 local model. Do NOT pull 7B/14B/72B for this talk.
set -euo pipefail

MODEL="${LOCAL_OLLAMA_TAG:-qwen2.5:0.5b}"
HOST="${OLLAMA_HOST:-http://localhost:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not on PATH."
  echo "Install: https://ollama.com/download"
  echo "Then re-run this script."
  exit 1
fi

echo "▸ using Ollama at ${HOST}"
echo "▸ pulling ${MODEL} (~398MB) — this is the only local model for v1"
ollama pull "${MODEL}"

echo "▸ warming ${MODEL} (first token after pull is the slow one — do this before doors)"
ollama run "${MODEL}" "Reply with the single word ready."

echo "▸ done. If that printed 'ready', the local path is hot."

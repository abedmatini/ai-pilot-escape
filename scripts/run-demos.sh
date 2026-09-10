#!/usr/bin/env bash
# Run seed prompts A–D. Use --dry-run to rehearse routing without keys.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
else
  PY="python3"
fi

DRY=()
EXTRA=()
for arg in "$@"; do
  if [[ "${arg}" == "--dry-run" ]]; then
    DRY=(--dry-run)
  else
    EXTRA+=("${arg}")
  fi
done

if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

run_one() {
  local label="$1"
  local scenario="$2"
  local -a cmd
  echo "======== ${label} ========"
  cmd=("${PY}" -m demo.router --scenario "${scenario}")
  if [[ ${#DRY[@]} -gt 0 ]]; then
    cmd+=("${DRY[@]}")
  fi
  if [[ ${#EXTRA[@]} -gt 0 ]]; then
    cmd+=("${EXTRA[@]}")
  fi
  "${cmd[@]}"
}

run_one "A easy → local" A
echo
run_one "B hard → cloud" B
echo
run_one "C PII redact → cloud" C
echo
run_one "D force-local → fallback" D

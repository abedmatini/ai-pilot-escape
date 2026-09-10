# Seed prompts A–D (stage cheat sheet)

Load any of these with:

```bash
python -m demo.router --scenario A
python -m demo.router --scenario B
python -m demo.router --scenario C
python -m demo.router --scenario D
```

`--dry-run` prints the route without calling a model (useful if Ollama is still warming).

| ID | Intent | Expected first hop | Files |
| --- | --- | --- | --- |
| **A** | Short email summarize | `local` · `qwen2.5:0.5b` · $0 | `demo/prompts/A_easy.md` |
| **B** | Multi-step architecture | `cloud` · `gemini/gemini-3.6-flash` | `demo/prompts/B_hard.md` |
| **C** | Customer email with PII | regex redact locally, then cloud on clean text | `demo/prompts/C_pii.md` |
| **D** | Same class as B, pinned local | local first (weak or error) → `fallback=true` cloud | `demo/prompts/D_force_local.md` |

## What you say on stage

- **A:** “Three-line email. We are not paying Flash for this.”
- **B:** “This is the work you actually want a frontier model for.”
- **C:** “Watch the placeholders. The raw ID and phone never leave the laptop.”
- **D:** “Force the 0.5B model to do architecture. Then we fall back — policy, not hope.”

## Optional extras

```bash
# Classify only
python -m demo.router --scenario A --dry-run

# Hit LiteLLM aliases instead of the Python SDK
python -m demo.router --scenario A --via-proxy

# Guarantee a transport fallback (stop Ollama first)
python -m demo.router --scenario A --force-local
```

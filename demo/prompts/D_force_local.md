# D — Force-local on a hard task → weak/fail → fallback cloud
# Run as: python -m demo.router --scenario D
# (scenario D implies --force-local and quality fallback)

Design a production-ready hybrid local-to-cloud LLM architecture for a Cape Town
fintech. This is a multi-step architecture design: classify easy vs hard prompts,
place a gateway with local/cloud/auto aliases, keep PII on the edge, and spell
out fallbacks, trade-offs, and failure modes. Compare heuristic routing vs a
learned semantic router and recommend what to ship first.

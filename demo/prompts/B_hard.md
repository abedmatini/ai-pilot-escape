# B — Hard → cloud (multi-step architecture)
# Expected: route=auto/cloud  model=gemini/gemini-3.6-flash

Design a production-ready hybrid local-to-cloud LLM architecture for a Cape Town fintech that must honour POPIA.

Do this as a multi-step architecture design:
1. Classify inbound prompts into easy (summarize, classify, JSON extract) vs hard (reasoning, system design).
2. Place a gateway with aliases `local`, `cloud`, and router-driven `auto`.
3. Keep PII redaction on the edge so raw customer data does not leave the network.
4. Spell out fallbacks when the local SLM is down or returns a weak answer.
5. List concrete trade-offs (cost, latency, quality, data residency) and failure modes.

Compare at least two routing approaches (heuristic vs learned / semantic) and recommend what to ship first.

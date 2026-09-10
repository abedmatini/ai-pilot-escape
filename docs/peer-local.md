# Bonus: one policy, a pool of local workers

This is **documentation and a stub**, not a second runtime. v1 succeeds with **one** Ollama on **one** machine. Do not install extra device runtimes to “finish” the talk.

## The idea

The router already thinks in **aliases**, not hostnames. Several approved machines can be deployments in one `local` pool:

```
application → policy router → local alias ─┬─ worker-a  your Ollama
                                           ├─ worker-b  approved laptop
                                           └─ worker-c  spare machine
                           ↘ cloud             hard work or controlled fallback
```

Each independent request goes to **one** healthy worker. This adds throughput and resilience; it does not make the local model more capable. The same easy/hard/PII policy still decides whether a request belongs in the local pool or cloud.

What you add later (not in v1):

1. More LiteLLM deployments with the **same** `model_name` and different `api_base` values.
2. A LiteLLM routing strategy, retries, cooldowns, and background health-check routing.
3. Discovery or inventory — static configuration, private DNS, a tailnet, mDNS, or a device fabric.
4. Device identity, authenticated transport, enrolment, ownership, patching, and audit.

## Light stub (config only)

Add entries like these when you actually have a second box. The checked-in config and CLI do **not** do this yet; that is intentional.

```yaml
#  - model_name: local
#    litellm_params:
#      model: ollama/qwen2.5:0.5b
#      api_base: http://192.168.1.50:11434
#
# router_settings:
#   routing_strategy: least-busy
#
# general_settings:
#   background_health_checks: true
#   enable_health_check_routing: true
```

LiteLLM can load-balance known deployments behind one model name. It is not a device-discovery or fleet-management system.

## Do not confuse pooling with model sharding

The film shows a worker pool:

- Request 1 can run on worker A.
- Request 2 can run on worker B while A is busy.
- Each worker holds and executes the complete local model.

Model sharding is different: one model generation is split across several machines. It requires a distributed inference runtime and fast, reliable links. LiteLLM does not perform that split.

## Relevant products and projects

This is an ecosystem, not a single interchangeable product category. These are examples, not endorsements.

### Gateway and request pooling

- [LiteLLM](https://docs.litellm.ai/docs/proxy/load_balancing) groups known deployments behind one model name and provides load balancing, retries, cooldowns, fallbacks, and health-check-driven routing. It does not enrol or discover laptops.
- [LocalAI](https://localai.io/docs/features/distribute/) exposes OpenAI-compatible local inference. Its federated mode discovers nodes using a shared P2P token and routes each request to one node. Its separate worker mode can shard llama.cpp-compatible models. Treat P2P federation as experimental/tech-preview functionality and validate its behavior before production use.

### Device and edge fabrics

- [mimik / mimOE](https://mimik.com/mimoe) combines on-device inference with device discovery, mesh connectivity, authentication/policy, lifecycle operations, and observability. It is broader than an LLM gateway.
- [KubeEdge with Sedna](https://release-1-12.docs.kubeedge.io/en/docs/subproject/sedna/) provides Kubernetes-style edge fleet orchestration and edge-cloud collaborative inference. It targets managed edge infrastructure rather than an informal laptop pool.

### Distributed model inference

- [exo](https://github.com/exo-explore/exo/) discovers nearby machines, evaluates topology, and shards models across their combined resources. It is closer to “make several machines act like one inference cluster” than LiteLLM. Treat API security as deployment work; cluster isolation is not the same as authenticated access.
- [llama.cpp RPC](https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md) can offload model computation across hosts, but its own documentation describes the RPC backend as experimental and insecure. Never expose it to an open or sensitive network.
- [Ray Serve](https://docs.ray.io/en/latest/serve/) provides multi-node model serving, replica scheduling, load balancing, and autoscaling on a managed Ray cluster. It is adjacent infrastructure, not ad-hoc peer discovery.

### Managed model serving

- [KServe](https://kserve.github.io/website/) provides production model lifecycle, health, autoscaling, and routing on Kubernetes. It represents the conventional managed-cluster end of the spectrum, not an opportunistic laptop mesh.

## Stage-safe wording

Mention the ecosystem once:

> “There is no one-for-one standard here. Projects such as mimOE and LocalAI explore peer-local inference fabrics; exo explores model splitting across local hardware; KServe represents the managed-cluster end. Our example is only the simplest pattern: known, approved inference workers behind one local alias.”

Then return to the architecture:

- “Local is a governed trust boundary, not necessarily this exact laptop.”
- “LiteLLM can select among known healthy endpoints; discovery and device governance sit outside it.”
- “This demo uses one Ollama node. The pool is an optional extension.”

### What not to say

- Pricing, discounts, or “the standard for edge AI.”
- “Our partner” / “we standardized on…”
- A live install, QR code, or feature tour.
- Anything that turns the bonus into a booth.
- That all of these tools solve the same layer.
- That pooling makes a weak model stronger.

## When not to tell this story

- You cannot name who is responsible for data on the other laptop.
- You need an audit trail a personal machine cannot give.
- Network transfer, cold starts, or coordination cost erase the expected savings.
- You are about to shard **hard** prompts merely to dodge a cloud invoice. That is quality theatre unless evaluation proves it.

## Talk hygiene

Skip this entire topic if the A–D demo ran long. The audience came for cost and routing, not a vendor comparison.

On stage, use slide 23 to explain the boundary, then optionally play the slide-24 film (`speaker/videos/slide-24__peer-mesh.mp4`). Cue: `speaker/visuals.md`.

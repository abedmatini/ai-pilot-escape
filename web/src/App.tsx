import { useEffect, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type Seed = {
  id: string;
  label: string;
  note: string;
  force_local: boolean;
  prompt: string;
};

type Telemetry = {
  route: string;
  reason: string;
  model: string;
  latency_ms: number;
  est_cost_usd: number;
  fallback: boolean;
  pii_redacted: boolean;
  pii_found: string[];
  difficulty: string;
};

type ChatResponse = {
  ok: boolean;
  error: string | null;
  completion: string;
  outgoing: string;
  local_preview: string | null;
  scenario: string;
  scenario_label: string;
  pii_found: string[];
  telemetry: Telemetry;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  forceLocal?: boolean;
  scenario?: string;
  scenarioLabel?: string;
  telemetry?: Telemetry;
  outgoing?: string;
  localPreview?: string | null;
  error?: string;
};

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatCost(n: number) {
  return n === 0 ? "$0" : `$${n.toFixed(6)}`;
}

export default function App() {
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [seedsError, setSeedsError] = useState("");
  const [draft, setDraft] = useState("");
  const [forceLocal, setForceLocal] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/seeds")
      .then((r) => {
        if (!r.ok) throw new Error(`seeds ${r.status}`);
        return r.json() as Promise<Seed[]>;
      })
      .then(setSeeds)
      .catch(() => setSeedsError("Could not load seed prompts. Is the chat server running?"));
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  function applySeed(seed: Seed) {
    setDraft(seed.prompt);
    setForceLocal(seed.force_local);
  }

  async function send() {
    const prompt = draft.trim();
    if (!prompt || busy) return;
    const user: Message = { id: uid(), role: "user", text: prompt, forceLocal };
    setMessages((m) => [...m, user]);
    setDraft("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          force_local: forceLocal,
          dry_run: dryRun,
        }),
      });
      const data = (await res.json()) as ChatResponse;
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          text: data.ok
            ? data.completion || (dryRun ? "Route only — no model call." : "")
            : data.error || "That turn failed.",
          scenario: data.scenario,
          scenarioLabel: data.scenario_label,
          telemetry: data.telemetry,
          outgoing: data.outgoing,
          localPreview: data.local_preview,
          error: data.ok ? undefined : data.error || "That turn failed.",
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          text: "Could not reach the router. Start it with ./scripts/start-chat.sh",
          error: "network",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-3xl flex-col px-4 py-6 sm:px-6">
      <header className="mb-5 border-b border-[#37393B] pb-4">
        <p className="mb-1 text-[11px] font-bold tracking-[0.16em] text-[#BB2028] uppercase">
          Hybrid router · demo chat
        </p>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Stop paying for easy prompts
        </h1>
        <p className="mt-2 text-sm text-[#8F8F8F]">
          Type anything. The same policy as the CLI picks A, B, or C. Use{" "}
          <span className="text-[#CFCFCF]">Force local</span> to run D.
        </p>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {seeds.map((seed) => (
          <Button
            key={seed.id}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => applySeed(seed)}
          >
            {seed.id} · {seed.note}
          </Button>
        ))}
      </div>
      {seedsError ? <p className="mb-4 text-sm text-[#FF0000]">{seedsError}</p> : null}

      <main className="flex min-h-0 flex-1 flex-col gap-4">
        {messages.length === 0 && !busy ? (
          <div className="rounded-lg border border-dashed border-[#555555] bg-[#060608] px-4 py-10 text-center text-sm text-[#8F8F8F]">
            Empty thread. Load a seed above, or type a standup summary, an
            architecture brief, or a customer email with fake PII.
          </div>
        ) : null}

        {messages.map((msg) => (
          <article
            key={msg.id}
            className={
              msg.role === "user"
                ? "ml-auto max-w-[92%] rounded-lg border border-[#37393B] bg-[#060608] px-4 py-3 sm:max-w-[80%]"
                : "mr-auto max-w-[92%] rounded-lg border border-[#37393B] bg-[#000000] px-4 py-3 sm:max-w-[80%]"
            }
          >
            <p className="mb-1 text-[11px] font-bold tracking-wider text-[#8F8F8F] uppercase">
              {msg.role === "user" ? "You" : "Router"}
              {msg.role === "user" && msg.forceLocal ? " · force local" : ""}
            </p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#F5F5F5]">
              {msg.text}
            </p>
            {msg.role === "assistant" && msg.scenario ? (
              <div className="mt-3 space-y-2 border-t border-[#37393B] pt-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>Scenario {msg.scenario}</Badge>
                  <span className="text-sm text-[#CFCFCF]">{msg.scenarioLabel}</span>
                </div>
                {msg.telemetry ? (
                  <p className="font-mono text-xs leading-relaxed text-[#8F8F8F]">
                    {msg.telemetry.route} · {msg.telemetry.model} ·{" "}
                    {formatCost(msg.telemetry.est_cost_usd)} ·{" "}
                    {msg.telemetry.latency_ms}ms
                    {msg.telemetry.fallback ? " · fallback=true" : ""}
                    {msg.telemetry.pii_redacted ? " · redacted" : ""}
                  </p>
                ) : null}
                {msg.telemetry?.pii_redacted && msg.outgoing ? (
                  <p className="text-xs text-[#8F8F8F]">
                    What may leave: {msg.outgoing.slice(0, 220)}
                    {msg.outgoing.length > 220 ? "…" : ""}
                  </p>
                ) : null}
                {msg.localPreview ? (
                  <p className="text-xs text-[#8F8F8F]">
                    Local first (thin): {msg.localPreview.slice(0, 180)}
                    {msg.localPreview.length > 180 ? "…" : ""}
                  </p>
                ) : null}
                {msg.error ? (
                  <p className="text-sm text-[#FF0000]">{msg.error}</p>
                ) : null}
              </div>
            ) : null}
          </article>
        ))}

        {busy ? (
          <p className="text-sm text-[#8F8F8F]" aria-live="polite">
            Routing…
          </p>
        ) : null}
        <div ref={bottom} />
      </main>

      <form
        className="sticky bottom-0 mt-5 space-y-3 border-t border-[#37393B] bg-black pt-4 pb-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask for a one-line summary, a hybrid architecture, or paste synthetic PII…"
          rows={4}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-4 text-sm text-[#CFCFCF]">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={forceLocal}
                onChange={(e) => setForceLocal(e.target.checked)}
                className="accent-[#BB2028]"
              />
              Force local (D)
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
                className="accent-[#BB2028]"
              />
              Route only
            </label>
          </div>
          <Button type="submit" disabled={busy || !draft.trim()}>
            Send
          </Button>
        </div>
        <p className="text-xs text-[#555555]">⌘/Ctrl + Enter to send</p>
      </form>
    </div>
  );
}

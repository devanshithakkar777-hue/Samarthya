"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Note } from "@/components/kit/Controls";
import CrisisBox from "@/components/live/CrisisBox";

type Cite = { title: string; path: string; source: { url: string; title: string; publisher: string } | null };
type Out = { mode: "ai" | "retrieval" | "safety"; answer: string; citations: Cite[]; crisis_resources?: React.ComponentProps<typeof CrisisBox>["c"]["resources"]; note?: string };

export default function Companion() {
  const status = useMine<{ ai_enabled: boolean; daily_limit: number }>("/v1/me/companion/status");
  const [q, setQ] = useState("");
  const [log, setLog] = useState<{ q: string; out: Out }[]>([]);
  const { busy, error, run } = useAction();
  async function ask(e: React.FormEvent) { e.preventDefault(); const question = q; const out = await run(() => call<Out>("POST", "/v1/me/companion", { question })); if (out) { setLog([{ q: question, out }, ...log]); setQ(""); } }
  return (
    <div className="grid max-w-3xl gap-5">
      <Note>{status.data?.ai_enabled ? "Answers are written by an AI from Samarthya's sourced pages, and may be wrong. Anything not marked as sourced is a suggestion. Check important details on the official page." : "AI writing is switched off on this site. You get the closest sourced passages instead, copied as they are."} The companion does not remember past chats, does not diagnose anything, and is not a replacement for people.</Note>
      <form onSubmit={ask} className="grid gap-3"><label htmlFor="cq" className="font-medium">Ask about careers, skills, study or applications</label><textarea id="cq" rows={3} className={inp} required minLength={3} maxLength={600} value={q} onChange={(e) => setQ(e.target.value)} />
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>{busy ? "Thinking…" : "Ask"}</button></div></form>
      <div aria-live="polite" className="grid gap-4">{log.map((l, i) => (
        <section key={i} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5"><p className="text-sm text-slate">You asked: {l.q}</p>
          {l.out.mode === "safety" && l.out.crisis_resources && <div className="mt-3"><CrisisBox c={{ message: l.out.answer, resources: l.out.crisis_resources }} /></div>}
          {l.out.mode !== "safety" && <><p className="mt-2 whitespace-pre-line text-lg">{l.out.answer}</p>
            {l.out.citations.length > 0 && <ul className="mt-3 grid gap-1 text-sm text-slate">{l.out.citations.map((c) => <li key={c.path}>From <Link className="text-electric-blue underline" href={c.path}>{c.title}</Link>{c.source ? <> · <a className="text-electric-blue underline" href={c.source.url} target="_blank" rel="noopener noreferrer">{c.source.publisher}<span className="sr-only"> (opens in a new tab)</span></a></> : null}</li>)}</ul>}
            {l.out.mode === "ai" && <p className="mt-2 text-xs text-slate">AI-written. {l.out.note}</p>}</>}</section>))}</div>
    </div>
  );
}

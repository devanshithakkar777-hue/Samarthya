"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { fmtDate, btn } from "./ui";

type Cite = { title: string; path: string; source: { url: string; title: string; publisher: string } | null; last_verified: string | null; stale: boolean };
type Out = { answered: boolean; answer: string; citations: Cite[]; link?: string };

const EXAMPLES = ["What does a data analyst need?", "Which degree leads to this role?", "Where can I apply?"];

export default function AskBox() {
  const [q, setQ] = useState("");
  const [out, setOut] = useState<Out | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  async function ask(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setOut(null); setBusy(true);
    try { setOut(await call<Out>("POST", "/v1/ask", { question: q })); } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }
  return (
    <div className="max-w-2xl">
      <form onSubmit={ask} className="grid gap-3">
        <label htmlFor="q" className="text-lg font-semibold">Ask about a career, degree or skill</label>
        <input id="q" required minLength={3} maxLength={300} className="w-full rounded-md border border-slate/50 bg-white px-3 py-3" value={q} onChange={(e) => setQ(e.target.value)} placeholder={EXAMPLES[0]} />
        <div><button className={btn} disabled={busy}>{busy ? "Looking…" : "Ask"}</button></div>
        <p className="text-sm text-slate">Answers are copied from Samarthya&apos;s sourced pages. This is not a chatbot that makes things up: if we do not have a sourced answer, it says so.</p>
      </form>
      <div aria-live="polite" className="mt-6">
        {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
        {out && (
          <div className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
            <p className="text-lg">{out.answer}</p>
            {out.citations.length > 0 && (
              <ul className="mt-4 grid gap-2 text-sm text-slate">
                {out.citations.map((c) => (
                  <li key={c.path + c.title}>
                    From <Link className="text-electric-blue underline" href={c.path}>{c.title}</Link>
                    {c.source && <>. Source: <a className="text-electric-blue underline" href={c.source.url} target="_blank" rel="noopener noreferrer">{c.source.title}<span className="sr-only"> (opens in a new tab)</span></a>, {c.source.publisher}</>}
                    . Last checked {fmtDate(c.last_verified)}.{c.stale && <strong className="ml-1 rounded bg-ink px-2 py-0.5 text-arctic-white">May be out of date</strong>}
                  </li>
                ))}
              </ul>
            )}
            {!out.answered && <p className="mt-4 text-sm">You can <Link className="text-electric-blue underline" href="/explore">browse careers</Link> or <Link className="text-electric-blue underline" href="/report">tell us what is missing</Link>.</p>}
          </div>
        )}
      </div>
    </div>
  );
}

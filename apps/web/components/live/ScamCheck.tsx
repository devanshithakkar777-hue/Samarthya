"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";

type Flag = { id: string; level: string; title: string; why: string; source: string; matched: string };
type R = { verdict: string; summary: string; flags: Flag[]; help: { report: string; verify: string }; note: string };

export default function ScamCheck() {
  const [text, setText] = useState("");
  const [out, setOut] = useState<R | null>(null);
  const { busy, error, run } = useAction();
  async function go(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<R>("POST", "/v1/tools/scam-check", { text }));
    if (r) setOut(r);
  }
  return (
    <div className="max-w-3xl">
      <Note>Paste a job, internship, scholarship or payment message. The check looks for patterns that official bodies warn about. It runs on our server, nothing you paste is saved, and it can never tell you an offer is genuine. Do not paste passwords, OTPs or card numbers.</Note>
      <form onSubmit={go} className="mt-4 grid gap-3">
        <Labeled id="scam-text" label="The message"><textarea id="scam-text" rows={8} className={inp} value={text} onChange={(e) => setText(e.target.value)} required minLength={10} maxLength={6000} /></Labeled>
        <ErrorText>{error}</ErrorText>
        <div><button className={btn} disabled={busy || text.trim().length < 10}>Check this message</button></div>
      </form>
      {out && (
        <div className="mt-6" aria-live="polite">
          <h2 className="text-xl font-semibold">{out.verdict === "many_flags" ? "Several warning signs" : out.verdict === "some_flags" ? "Some warning signs" : "No warning signs found"}</h2>
          <p className="mt-1">{out.summary}</p>
          {out.flags.length > 0 && <ul className="mt-4 grid gap-3">{out.flags.map((f) => (
            <li key={f.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-semibold">{f.title} <span className="ml-2 rounded bg-ink px-2 py-0.5 text-xs font-normal text-arctic-white">{f.level}</span></p>
              <p className="text-sm text-slate">Found: &ldquo;{f.matched}&rdquo;</p><p className="mt-1 text-sm">{f.why}</p>
              <p className="mt-1 text-xs"><a className="text-electric-blue underline" href={f.source} target="_blank" rel="noopener noreferrer">Official source<span className="sr-only"> (opens in a new tab)</span></a></p></li>))}</ul>}
          <h3 className="mt-6 font-semibold">What to do</h3>
          <p className="mt-1">{out.help.verify}</p><p className="mt-1">{out.help.report}</p>
          <p className="mt-3 text-sm text-slate">{out.note}</p>
        </div>)}
    </div>
  );
}

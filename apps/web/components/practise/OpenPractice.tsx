"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Note, small } from "@/components/kit/Controls";

type Q = { id: number; stem: string; topic: string };
type Next = { question: Q | null; message?: string };
type Check = { kind: string; message: string };
type Out = { guidance: string | null; automatic_checks: Check[]; ai_feedback: { strengths?: string[]; improvements?: string[] } | null; ai_note: string | null; note: string };
const SELF = ["clarity", "depth", "relevance", "confidence"];

export default function OpenPractice({ pillar }: { pillar: string }) {
  const { data, reload, error } = useMine<Next>(`/v1/me/practice/open/next?pillar=${encodeURIComponent(pillar)}`);
  const ai = useMine<{ ai_enabled: boolean }>("/v1/me/companion/status");
  const [answer, setAnswer] = useState("");
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [useAi, setUseAi] = useState(false);
  const [out, setOut] = useState<Out | null>(null);
  const { busy, error: err, run } = useAction();
  const q = data?.question;
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p role="status">Loading…</p>;
  if (!q) return <Note>{data.message ?? "No question available."}</Note>;
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<Out>("POST", "/v1/me/practice/open/answer", { question_id: q!.id, answer, ratings, use_ai: useAi }));
    if (r) setOut(r);
  }
  async function next() { setOut(null); setAnswer(""); setRatings({}); await reload(); }
  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold">{q.stem}</h2>
      {!out ? (
        <form onSubmit={submit} className="mt-4 grid gap-4">
          <div><label htmlFor="ans" className="font-medium">Your answer</label><textarea id="ans" rows={8} required className={inp} value={answer} onChange={(e) => setAnswer(e.target.value)} /></div>
          {ai.data?.ai_enabled && <label className="flex items-center gap-2"><input type="checkbox" className="h-5 w-5 accent-electric-blue" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />Also ask AI for feedback (AI-written, may be wrong)</label>}
          <ErrorText>{err}</ErrorText>
          <div><button className={btn} disabled={busy}>{busy ? "Checking…" : "Check my answer"}</button></div>
        </form>
      ) : (
        <div className="mt-4 grid gap-4" aria-live="polite">
          {out.guidance && <div className="rounded-md border border-ink/10 bg-white p-4"><h3 className="font-semibold">What a strong answer covers</h3><p className="mt-1 whitespace-pre-line">{out.guidance}</p></div>}
          {out.automatic_checks.length > 0 && <div><h3 className="font-semibold">Structure checks</h3><ul className="list-disc pl-5">{out.automatic_checks.map((c, i) => <li key={i}>{c.message}</li>)}</ul></div>}
          {out.ai_feedback && <div className="rounded-md border border-ink/10 bg-white p-4"><h3 className="font-semibold">AI feedback (AI-written)</h3>
            {out.ai_feedback.strengths?.length ? <><p className="mt-1 text-sm font-medium">Strengths</p><ul className="list-disc pl-5">{out.ai_feedback.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></> : null}
            {out.ai_feedback.improvements?.length ? <><p className="mt-1 text-sm font-medium">To improve</p><ul className="list-disc pl-5">{out.ai_feedback.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul></> : null}</div>}
          {out.ai_note && <Note>{out.ai_note}</Note>}
          <Note>{out.note}</Note>
          <button className={btn} onClick={next}>Another question</button>
        </div>
      )}
    </div>
  );
}

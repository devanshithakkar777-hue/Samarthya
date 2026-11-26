"use client";

import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, Note } from "@/components/kit/Controls";

type Q = { id: number; stem: string; options: string[] };
type Start = { attempt_id: number; title: string; duration_minutes: number | null; questions: Q[] };
type Done = { score_pct: number; correct: number; total: number; by_topic: Record<string, { correct: number; total: number }>; over_time_limit: boolean; credential_statement: string;
  review: { question_id: number; stem: string; options: string[]; chosen: number | null; correct_index: number; correct: boolean; explanation: string }[] };

export default function Assessment({ slug, duration }: { slug: string; duration: number | null }) {
  const [s, setS] = useState<Start | null>(null);
  const [ans, setAns] = useState<Record<string, number>>({});
  const [done, setDone] = useState<Done | null>(null);
  const [left, setLeft] = useState<number | null>(null);
  const { busy, error, run } = useAction();
  useEffect(() => { if (!s || done || !duration) return; const end = Date.now() + duration * 60000; const id = setInterval(() => setLeft(Math.max(0, Math.round((end - Date.now()) / 1000))), 1000); return () => clearInterval(id); }, [s, done, duration]);
  async function start() { const r = await run(() => call<Start>("POST", `/v1/me/assessments/${slug}/start`)); if (r) { setS(r); setAns({}); setDone(null); } }
  async function submit() { const r = await run(() => call<Done>("POST", `/v1/me/assessments/attempts/${s!.attempt_id}/submit`, { answers: ans })); if (r) setDone(r); }
  if (!s) return <div><Note>You can take this as many times as you like. Your result is private to you.</Note><button className={`${btn} mt-4`} onClick={start} disabled={busy}>Start</button><ErrorText>{error}</ErrorText></div>;
  if (done) return (
    <div className="max-w-2xl" aria-live="polite">
      <h2 className="text-2xl font-semibold">{done.correct} of {done.total} correct ({done.score_pct}%)</h2>
      {done.over_time_limit && <p className="mt-1 text-sm text-slate">You went past the suggested time. The score still counts; time limits here are for practice.</p>}
      <Note>{done.credential_statement}</Note>
      <h3 className="mt-6 text-lg font-semibold">By topic</h3><ul className="list-disc pl-5">{Object.entries(done.by_topic).map(([t, v]) => <li key={t}>{t}: {v.correct}/{v.total}</li>)}</ul>
      <h3 className="mt-6 text-lg font-semibold">Review</h3>
      <ol className="mt-2 grid gap-4">{done.review.map((r) => (<li key={r.question_id} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{r.stem}</p>
        <p className="mt-1 text-sm">{r.correct ? "Correct." : r.chosen === null ? "Not answered." : `You chose: ${r.options[r.chosen]}.`} Right answer: {r.options[r.correct_index]}.</p><p className="mt-1 text-sm text-slate">{r.explanation}</p></li>))}</ol>
      <div className="mt-6 flex gap-3"><button className={btn} onClick={start}>Take it again</button><a className="rounded-md border border-electric-blue px-5 py-3 font-medium text-electric-blue" href="/api/proxy/v1/me/transcript.pdf">Download my transcript (PDF)</a></div>
    </div>
  );
  return (
    <div className="max-w-2xl">
      {left !== null && <p role="timer" className="mb-4 rounded bg-white p-2 text-sm">Suggested time left: {Math.floor(left / 60)}:{String(left % 60).padStart(2, "0")}</p>}
      <ol className="grid gap-6">{s.questions.map((q) => (<li key={q.id}><fieldset><legend className="font-medium">{q.stem}</legend>
        <ul className="mt-2 grid gap-2">{q.options.map((o, i) => (<li key={i}><label className="flex cursor-pointer items-start gap-3 rounded-md border border-ink/20 bg-white p-3"><input type="radio" name={`q${q.id}`} className="mt-1 accent-electric-blue" checked={ans[String(q.id)] === i} onChange={() => setAns({ ...ans, [String(q.id)]: i })} />{o}</label></li>))}</ul></fieldset></li>))}</ol>
      <ErrorText>{error}</ErrorText>
      <button className={`${btn} mt-6`} onClick={submit} disabled={busy}>Submit answers</button>
    </div>
  );
}

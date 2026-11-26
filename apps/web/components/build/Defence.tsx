"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Note, small } from "@/components/kit/Controls";

type Q = { entry_id: number; topic: string; source_line: string; question: string };
type R = { id: number; title: string };
type Ready = { answers_practised: number; open_questions_practised: number; topics: { topic: string; average_self_rating: number; answers: number }[]; repeated_feedback: { kind: string; times: number }[]; note: string };

export default function Defence({ resume }: { resume?: string }) {
  const resumes = useMine<{ id: number; name: string }[]>("/v1/me/resumes");
  const [rid, setRid] = useState(resume ?? "");
  const [level, setLevel] = useState("5");
  const [mode, setMode] = useState("practice");
  const qs = useMine<{ questions: (Q & { hint?: string; level?: number })[]; note: string; time_limit_seconds?: number | null; levels?: Record<string, string> }>(rid ? `/v1/me/resumes/${rid}/defence?level=${level}&mode=${mode}` : null);
  const ready = useMine<Ready>("/v1/me/defence/readiness");
  const [i, setI] = useState(0);
  const [answer, setAnswer] = useState("");
  const [scores, setScores] = useState<Record<string, number>>({});
  const [out, setOut] = useState<{ automatic_checks: { message: string }[]; note: string; dimensions?: Record<string, string>; follow_up?: string } | null>(null);
  const { busy, error, run } = useAction();
  const list = qs.data?.questions ?? [];
  const q = list[i % Math.max(list.length, 1)];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<typeof out>("POST", "/v1/me/defence/answers", { resume_id: Number(rid), entry_id: q.entry_id, topic: q.topic, question: q.question, answer, self_scores: scores }));
    if (r) { setOut(r); await ready.reload(); }
  }
  return (
    <div className="grid max-w-3xl gap-8">
      <Note>Every question comes from something you wrote. If you cannot answer one honestly, change the resume, not the answer.</Note>
      <div><label htmlFor="rid" className="font-medium">Which resume?</label><select id="rid" className={inp} value={rid} onChange={(e) => { setRid(e.target.value); setI(0); setOut(null); }}><option value="">Choose…</option>{(resumes.data ?? []).map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>
      {rid && <div className="grid gap-3 sm:grid-cols-2">
        <div><label htmlFor="lvl" className="font-medium">How hard?</label><select id="lvl" className={inp} value={level} onChange={(e) => { setLevel(e.target.value); setI(0); setOut(null); }}>{Object.entries(qs.data?.levels ?? { "1": "Explain it", "2": "Justify the choices", "3": "Defend the numbers and claims", "4": "Prove it or drop it", "5": "Cross-question under pressure" }).map(([k, v]) => <option key={k} value={k}>Level {k}: {v}</option>)}</select></div>
        <div><label htmlFor="mode" className="font-medium">Mode</label><select id="mode" className={inp} value={mode} onChange={(e) => { setMode(e.target.value); setOut(null); }}><option value="study">Study (hints shown)</option><option value="practice">Practice (feedback after)</option><option value="simulation">Simulation (about two minutes, no hints)</option></select></div></div>}
      {rid && list.length === 0 && !qs.loading && <Note>No questions yet. Choose some entries for this resume first.</Note>}
      {q && (
        <section aria-labelledby="q"><p className="text-sm text-slate">Question {(i % list.length) + 1} of {list.length} · {q.topic} · from &ldquo;{q.source_line}&rdquo;</p>
          <h2 id="q" className="mt-1 text-xl font-semibold">{q.question}</h2>
          {mode === "study" && q.hint && <p className="mt-1 text-sm text-slate">Hint: {q.hint}</p>}
          {mode === "simulation" && qs.data?.time_limit_seconds && <p className="mt-1 text-sm text-slate">Aim to answer in about {Math.round(qs.data.time_limit_seconds / 60)} minutes. There is no timer pressure here; it is only a guide.</p>}
          {!out ? (
            <form onSubmit={submit} className="mt-4 grid gap-4"><div><label htmlFor="a" className="font-medium">Your answer, as you would say it</label><textarea id="a" rows={6} required className={inp} value={answer} onChange={(e) => setAnswer(e.target.value)} /></div>
              <fieldset><legend className="font-medium">How was that, honestly? (1 to 5, optional)</legend><div className="mt-2 grid gap-2 sm:grid-cols-2">{["clarity", "depth", "honesty", "confidence"].map((k) => (
                <label key={k} className="flex items-center justify-between rounded-md border border-ink/10 bg-white px-3 py-2 capitalize">{k}<select aria-label={k} className="rounded border border-slate/50 px-2" value={scores[k] ?? ""} onChange={(e) => setScores({ ...scores, [k]: Number(e.target.value) })}><option value="">-</option>{[1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}</select></label>))}</div></fieldset>
              <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Save and see checks</button></div></form>
          ) : (
            <div className="mt-4 grid gap-3" aria-live="polite">{out.dimensions && <ul className="grid gap-1 sm:grid-cols-2">{Object.entries(out.dimensions).map(([k, v]) => <li key={k} className="rounded-md border border-ink/10 bg-white px-3 py-2 text-sm capitalize">{k}: <span className="normal-case">{v}</span></li>)}</ul>}{out.follow_up && <p className="rounded-md bg-ice-blue/40 p-3"><strong>Follow-up:</strong> {out.follow_up}</p>}{out.automatic_checks.length > 0 ? <ul className="list-disc pl-5">{out.automatic_checks.map((c, k) => <li key={k}>{c.message}</li>)}</ul> : <p>No structure issues spotted.</p>}<Note>{out.note}</Note>
              <button className={btn} onClick={() => { setOut(null); setAnswer(""); setScores({}); setI(i + 1); }}>Next question</button></div>)}
        </section>)}
      {ready.data && ready.data.answers_practised > 0 && (
        <section aria-labelledby="rd"><h2 id="rd" className="text-xl font-semibold">Where you stand</h2><p className="text-sm text-slate">{ready.data.note}</p>
          <p className="mt-2">{ready.data.answers_practised} answers practised.</p>
          {ready.data.topics.length > 0 && <ul className="mt-2 list-disc pl-5">{ready.data.topics.map((t) => <li key={t.topic}>{t.topic}: you rated yourself {t.average_self_rating}/5 across {t.answers}</li>)}</ul>}
          {ready.data.repeated_feedback.length > 0 && <p className="mt-2 text-sm">Checks that came up more than once: {ready.data.repeated_feedback.map((f) => `${f.kind} (${f.times}x)`).join(", ")}.</p>}</section>)}
      <button className={`${small} w-fit`} onClick={() => ready.reload()}>Refresh</button>
    </div>
  );
}

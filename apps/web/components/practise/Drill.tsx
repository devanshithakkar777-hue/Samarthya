"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Note, small } from "@/components/kit/Controls";

type Q = { id: number; stem: string; options: string[]; topic: string; difficulty: number };
type Next = { question: Q | null; message?: string; your_level?: number };
type Ans = { correct: boolean; correct_index: number; explanation: string; your_level: number; topic_accuracy: number; new_badges: { title: string }[] };
type Topic = { topic: string; questions: number; level: number; accuracy: number | null };

export default function Drill({ pillar, topic, pillars }: { pillar: string; topic?: string; pillars: Record<string, string> }) {
  const [p, setP] = useState(pillar);
  const [t, setT] = useState(topic ?? "");
  const [started, setStarted] = useState(!!topic);
  const topics = useMine<Topic[]>(`/v1/me/practice/topics?pillar=${encodeURIComponent(p)}`);
  return (
    <div>
      {!started ? (
        <div className="grid max-w-2xl gap-4">
          <div><label htmlFor="pillar" className="font-medium">Area</label>
            <select id="pillar" className={inp} value={p} onChange={(e) => { setP(e.target.value); setT(""); }}>{Object.entries(pillars).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>
          <ErrorText>{topics.error}</ErrorText>
          {(topics.data ?? []).length === 0 && !topics.loading ? <Note>No questions are published in this area yet. They appear only after they have been written with an explanation and checked by a second person.</Note> : (
            <ul className="grid gap-2">{(topics.data ?? []).map((x) => (
              <li key={x.topic} className="flex items-center justify-between rounded-md border border-ink/10 bg-white p-3">
                <span><strong>{x.topic}</strong><span className="ml-2 text-sm text-slate">{x.questions} questions · level {x.level}{x.accuracy !== null ? ` · ${x.accuracy}% so far` : ""}</span></span>
                <button className={small} onClick={() => { setT(x.topic); setStarted(true); }}>Practise</button></li>))}</ul>)}
        </div>
      ) : <Session pillar={p} topic={t} stop={() => setStarted(false)} />}
    </div>
  );
}

function Session({ pillar, topic, stop }: { pillar: string; topic: string; stop: () => void }) {
  const { data, reload, error } = useMine<Next>(`/v1/me/practice/next?pillar=${encodeURIComponent(pillar)}&topic=${encodeURIComponent(topic)}`);
  const [chosen, setChosen] = useState<number | null>(null);
  const [res, setRes] = useState<Ans | null>(null);
  const { busy, error: err, run } = useAction();
  const q = data?.question;
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p role="status">Loading…</p>;
  if (!q) return <div><Note>{data.message ?? "No question available."}</Note><button className={`${small} mt-4`} onClick={stop}>Back</button></div>;
  async function submit() {
    const r = await run(() => call<Ans>("POST", "/v1/me/practice/answer", { question_id: q!.id, chosen }));
    if (r) setRes(r);
  }
  async function next() { setRes(null); setChosen(null); await reload(); }
  return (
    <div className="max-w-2xl">
      <p className="text-sm text-slate">{topic} · your level {data.your_level ?? 1}</p>
      <fieldset className="mt-2" disabled={!!res}>
        <legend className="text-xl font-semibold">{q.stem}</legend>
        <ul className="mt-4 grid gap-2">{q.options.map((o, i) => {
          const mark = res ? (i === res.correct_index ? "border-electric-blue bg-white" : i === chosen ? "border-ink bg-white" : "border-ink/10 bg-white/60") : "border-ink/20 bg-white";
          return (<li key={i}><label className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 ${mark}`}>
            <input type="radio" name="opt" checked={chosen === i} onChange={() => setChosen(i)} className="mt-1 accent-electric-blue" /><span>{o}{res && i === res.correct_index && <strong className="ml-2">Correct answer</strong>}{res && i === chosen && i !== res.correct_index && <strong className="ml-2">Your answer</strong>}</span></label></li>);
        })}</ul>
      </fieldset>
      <ErrorText>{err}</ErrorText>
      {res ? (
        <div className="mt-4" aria-live="polite">
          <p className="text-lg font-semibold">{res.correct ? "Correct." : "Not this time."}</p>
          <p className="mt-1">{res.explanation}</p>
          <p className="mt-2 text-sm text-slate">Accuracy in this topic: {res.topic_accuracy}%. Your level: {res.your_level}.{res.new_badges.length > 0 && ` New badge: ${res.new_badges.map((b) => b.title).join(", ")}.`}</p>
          <div className="mt-4 flex gap-3"><button className={btn} onClick={next}>Next question</button><button className={small} onClick={stop}>Stop here</button></div>
        </div>
      ) : <div className="mt-4 flex gap-3"><button className={btn} onClick={submit} disabled={chosen === null || busy}>Check answer</button><button className={small} onClick={stop}>Stop here</button></div>}
    </div>
  );
}

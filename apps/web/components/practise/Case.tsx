"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, Note, small } from "@/components/kit/Controls";

type Scene = { key: string; text: string; end: boolean; debrief: string | null; choices: { index: number; label: string }[] };
type Start = { run_id: number; title: string; brief: string; dimensions: string[]; scene: Scene };
type Step = { consequence: string; scene: Scene; scores: Record<string, number>; finished?: boolean; summary?: { dimensions: Record<string, number>; note: string } };

export default function Case({ slug, note }: { slug: string; note: string }) {
  const [run, setRun] = useState<Start | null>(null);
  const [scene, setScene] = useState<Scene | null>(null);
  const [log, setLog] = useState<{ choice: string; consequence: string }[]>([]);
  const [fin, setFin] = useState<Step | null>(null);
  const { busy, error, run: act } = useAction();
  async function start() { const r = await act(() => call<Start>("POST", `/v1/me/scenarios/${slug}/start`)); if (r) { setRun(r); setScene(r.scene); setLog([]); setFin(null); } }
  async function choose(i: number, label: string) {
    const r = await act(() => call<Step>("POST", `/v1/me/scenarios/runs/${run!.run_id}/choose`, { choice: i }));
    if (r) { setLog([...log, { choice: label, consequence: r.consequence }]); setScene(r.scene); if (r.finished) setFin(r); }
  }
  if (!run) return (<div><Note>{note}</Note><button className={`${btn} mt-4`} onClick={start} disabled={busy}>Start the case</button><ErrorText>{error}</ErrorText></div>);
  return (
    <div className="max-w-2xl">
      <p className="mb-4 text-slate">{run.brief}</p>
      {log.map((l, i) => (<div key={i} className="mb-3 rounded-md border border-ink/10 bg-white p-3"><p className="text-sm text-slate">You chose</p><p className="font-medium">{l.choice}</p><p className="mt-1">{l.consequence}</p></div>))}
      {scene && (<div aria-live="polite"><p className="text-lg">{scene.text}</p>
        {!scene.end ? <ul className="mt-4 grid gap-2">{scene.choices.map((c) => <li key={c.index}><button className="w-full rounded-md border border-ink/20 bg-white p-3 text-left hover:border-electric-blue" disabled={busy} onClick={() => choose(c.index, c.label)}>{c.label}</button></li>)}</ul> : (
          <div className="mt-4 rounded-md border border-electric-blue bg-white p-4"><h3 className="font-semibold">Debrief</h3><p className="mt-1 whitespace-pre-line">{scene.debrief}</p>
            {fin?.summary && <><h4 className="mt-3 font-medium">How your choices leaned</h4><ul className="list-disc pl-5">{Object.entries(fin.summary.dimensions).map(([k, v]) => <li key={k}>{k}: {v > 0 ? "+" : ""}{v}</li>)}</ul><p className="mt-2 text-sm text-slate">{fin.summary.note}</p></>}
            <button className={`${small} mt-4`} onClick={start}>Try again</button></div>)}</div>)}
      <ErrorText>{error}</ErrorText>
    </div>
  );
}

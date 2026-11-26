"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, inp, Note, small } from "@/components/kit/Controls";
import CrisisBox, { type Crisis } from "./CrisisBox";

type E = { id: number; day: string; mood: number | null; body: string };
const MOODS = ["Very low", "Low", "Okay", "Good", "Very good"];

export default function Journal() {
  const list = useMine<{ entries: E[]; privacy: string }>("/v1/me/journal");
  const prompts = useMine<{ prompts: string[]; boundaries: string[] }>("/v1/me/journal/prompts");
  const mood = useMine<{ day: string; mood: number }[]>("/v1/me/journal/mood");
  const [body, setBody] = useState("");
  const [m, setM] = useState<number | null>(null);
  const [crisis, setCrisis] = useState<Crisis | null>(null);
  const { busy, error, run } = useAction();
  async function save(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<{ crisis?: boolean; message?: string; resources?: Crisis["resources"] }>("POST", "/v1/me/journal", { mood: m, body }));
    if (r) { setBody(""); setM(null); setCrisis(r.crisis && r.resources ? { message: r.message ?? "", resources: r.resources } : null); await list.reload(); await mood.reload(); }
  }
  const p = prompts.data?.prompts[new Date().getDate() % (prompts.data?.prompts.length || 1)];
  const series = mood.data ?? [];
  return (
    <div className="grid max-w-3xl gap-6">
      <Note>{list.data?.privacy ?? "Only you can read this. It is encrypted, never shared with institutions or employers, and never used for badges or streaks."}</Note>
      {crisis && <CrisisBox c={crisis} />}
      <form onSubmit={save} className="grid gap-4 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
        <fieldset><legend className="font-medium">How are you today? (optional)</legend><div className="mt-2 flex flex-wrap gap-2">{MOODS.map((l, i) => (
          <label key={l} className={`cursor-pointer rounded-md border px-3 py-1.5 text-sm ${m === i + 1 ? "border-electric-blue bg-electric-blue text-arctic-white" : "border-ink/20"}`}><input type="radio" name="mood" className="sr-only" checked={m === i + 1} onChange={() => setM(i + 1)} />{l}</label>))}</div></fieldset>
        <div><label htmlFor="jb" className="font-medium">Write if you like</label>{p && <p className="text-sm text-slate">Prompt: {p}</p>}<textarea id="jb" rows={6} className={inp} value={body} onChange={(e) => setBody(e.target.value)} maxLength={5000} /></div>
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy || (!body.trim() && m === null)}>Save entry</button></div>
      </form>
      {prompts.data && <ul className="list-disc pl-5 text-sm text-slate">{prompts.data.boundaries.map((b) => <li key={b}>{b}</li>)}</ul>}
      {series.length > 1 && (<section aria-labelledby="mt"><h2 id="mt" className="mb-2 text-lg font-semibold">Mood over the last 60 days</h2>
        <svg viewBox="0 0 300 80" role="img" aria-label={`Mood chart with ${series.length} days recorded, ranging from ${Math.min(...series.map((s) => s.mood))} to ${Math.max(...series.map((s) => s.mood))} out of 5`} className="h-24 w-full max-w-xl rounded border border-ink/10 bg-white">
          <polyline fill="none" stroke="currentColor" className="text-electric-blue" strokeWidth="2" points={series.map((s, i) => `${(i / (series.length - 1)) * 290 + 5},${75 - ((s.mood - 1) / 4) * 70}`).join(" ")} /></svg>
        <p className="mt-1 text-sm text-slate">Just a picture for you. It is not a measurement of anything, and nobody else sees it.</p></section>)}
      <section aria-labelledby="en"><h2 id="en" className="mb-3 text-lg font-semibold">Your entries</h2>
        {(list.data?.entries ?? []).length === 0 ? <p className="text-slate">Nothing yet.</p> : <ul className="grid gap-3">{(list.data?.entries ?? []).map((e) => (
          <li key={e.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="text-sm text-slate">{e.day}{e.mood ? ` · ${MOODS[e.mood - 1]}` : ""}</p><p className="mt-1 whitespace-pre-line">{e.body}</p>
            <button className={`${danger} mt-2`} onClick={async () => { if (window.confirm("Delete this entry for good?")) { await call("DELETE", `/v1/me/journal/${e.id}`); await list.reload(); await mood.reload(); } }}>Delete</button></li>))}</ul>}
        {(list.data?.entries ?? []).length > 0 && <button className={`${small} mt-4`} onClick={async () => { if (window.confirm("Delete your whole journal? This cannot be undone.")) { await call("DELETE", "/v1/me/journal"); await list.reload(); await mood.reload(); } }}>Delete my whole journal</button>}</section>
    </div>
  );
}

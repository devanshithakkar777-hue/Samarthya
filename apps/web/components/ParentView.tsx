"use client";

import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { ErrorText, Note } from "@/components/kit/Controls";

type V = { label: string | null; expires_on: string; note: string; activity?: { current: number; active_days_last_30: number }; badges?: { title: string; description: string }[]; badge_note?: string; topics?: { pillar: string; topic: string; attempts: number }[] };

export default function ParentView({ token }: { token: string }) {
  const [v, setV] = useState<V | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { call<V>("GET", `/v1/parent-view/${encodeURIComponent(token)}`).then(setV).catch((e) => setErr((e as Error).message)); }, [token]);
  if (err) return <ErrorText>{err}</ErrorText>;
  if (!v) return <p>Loading…</p>;
  return (
    <div className="grid max-w-2xl gap-4">
      <Note>{v.note} This link works until {v.expires_on}.</Note>
      {v.activity && <section aria-labelledby="pa"><h2 id="pa" className="text-xl font-semibold">Learning activity</h2><p>Active on {v.activity.active_days_last_30} of the last 30 days. Current run: {v.activity.current} day(s).</p></section>}
      {v.badges && <section aria-labelledby="pb"><h2 id="pb" className="text-xl font-semibold">Milestones earned</h2>{v.badges.length === 0 ? <p>None yet.</p> : <ul className="list-disc pl-5">{v.badges.map((b) => <li key={b.title}><strong>{b.title}</strong>: {b.description}</li>)}</ul>}<p className="mt-1 text-sm text-slate">{v.badge_note}</p></section>}
      {v.topics && <section aria-labelledby="pt"><h2 id="pt" className="text-xl font-semibold">Topics practised</h2>{v.topics.length === 0 ? <p>None yet.</p> : <ul className="list-disc pl-5">{v.topics.map((t, i) => <li key={i}>{t.topic} ({t.attempts} questions)</li>)}</ul>}</section>}
    </div>
  );
}

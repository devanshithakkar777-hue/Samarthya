"use client";

import { useMine } from "@/lib/useMine";
import { ErrorText, Note } from "./kit/Controls";

type D = { badges: { key: string; title: string; description: string; earned: boolean; awarded_on: string | null }[]; badge_note: string; streak: { current: number; best: number } | number;
  topics: { pillar: string; topic: string; level: number; attempts: number; accuracy: number | null }[]; counts: Record<string, number>; principle: string };

export default function Progress() {
  const { data, error, loading } = useMine<D>("/v1/me/progress");
  if (loading) return <p role="status">Loading…</p>;
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return null;
  const s = typeof data.streak === "number" ? { current: data.streak, best: data.streak } : data.streak;
  return (
    <div className="grid gap-8">
      <Note>{data.principle}</Note>
      <section aria-labelledby="c"><h2 id="c" className="mb-3 text-xl font-semibold">Your activity</h2>
        <dl className="grid grid-cols-2 gap-3 md:grid-cols-5">{Object.entries(data.counts).map(([k, v]) => (
          <div key={k} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4"><dt className="text-sm capitalize text-slate">{k.replace(/_/g, " ")}</dt><dd className="text-2xl font-semibold">{v}</dd></div>))}</dl>
        <p className="mt-3 text-sm text-slate">Current streak: {s?.current ?? 0} day(s). One missed day does not break it. Rest is part of learning.</p></section>
      <section aria-labelledby="t"><h2 id="t" className="mb-3 text-xl font-semibold">Topics</h2>
        {data.topics.length === 0 ? <p className="text-slate">Practise some questions and your topics appear here.</p> : (
          <table className="w-full max-w-3xl text-left text-sm"><caption className="sr-only">Practice by topic</caption><thead><tr className="border-b border-ink/20"><th className="py-2">Topic</th><th>Level</th><th>Answered</th><th>Accuracy</th></tr></thead>
            <tbody>{data.topics.map((t) => <tr key={t.pillar + t.topic} className="border-b border-ink/10"><td className="py-2">{t.topic}</td><td>{t.level}</td><td>{t.attempts}</td><td>{t.accuracy ?? "-"}%</td></tr>)}</tbody></table>)}</section>
      <section aria-labelledby="b"><h2 id="b" className="mb-1 text-xl font-semibold">Badges</h2><p className="mb-3 text-sm text-slate">{data.badge_note}</p>
        <ul className="grid gap-3 md:grid-cols-3">{data.badges.map((b) => (
          <li key={b.key} className={`rounded-[var(--radius-lg)] border p-4 ${b.earned ? "border-electric-blue bg-white" : "border-ink/10 bg-white/60"}`}>
            <h3 className="font-semibold">{b.title}{b.earned && <span className="ml-2 rounded bg-electric-blue px-2 py-0.5 text-xs text-arctic-white">Earned {b.awarded_on}</span>}</h3><p className="text-sm text-slate">{b.description}</p></li>))}</ul></section>
    </div>
  );
}

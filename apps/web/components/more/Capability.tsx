"use client";

import Link from "next/link";
import { useMine } from "@/lib/useMine";
import { ErrorText, Note } from "@/components/kit/Controls";

type D = { areas: { pillar: string; name: string; attempts: number; band: string; topics: { topic: string; attempts: number; accuracy: number | null; band: string }[] }[];
  plan: { pillar: string; topic: string; band: string; next: string; lessons: { slug: string; title: string; minutes: number }[] }[]; not_started: { pillar: string; name: string }[]; note: string };

export default function Capability() {
  const { data, error } = useMine<D>("/v1/me/capability");
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p role="status">Loading…</p>;
  return (
    <div className="grid max-w-3xl gap-6">
      <Note>{data.note}</Note>
      <section aria-labelledby="plan-h"><h2 id="plan-h" className="mb-2 text-2xl font-semibold">Your learning plan</h2>
        {data.plan.length === 0 ? <p>Answer a few practice questions and your plan appears here. <Link className="text-electric-blue underline" href="/practise/drill">Start practising</Link></p> :
          <ul className="grid gap-3">{data.plan.map((p) => <li key={p.pillar + p.topic} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{p.topic} <span className="text-sm text-slate">({p.pillar}, {p.band})</span></p><p className="text-sm text-slate">{p.next}</p>
            {p.lessons.length > 0 && <ul className="mt-1 list-disc pl-5 text-sm">{p.lessons.map((l) => <li key={l.slug}><Link className="text-electric-blue underline" href={`/academy/${l.slug}`}>{l.title}</Link> · {l.minutes} min</li>)}</ul>}</li>)}</ul>}</section>
      <section aria-labelledby="cap-h"><h2 id="cap-h" className="mb-2 text-2xl font-semibold">Where you are, area by area</h2>
        <ul className="grid gap-3 sm:grid-cols-2">{data.areas.map((a) => <li key={a.pillar} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{a.name}</p><p className="text-sm text-slate">{a.band} · {a.attempts} answers</p>
          <ul className="mt-1 text-sm">{a.topics.map((t) => <li key={t.topic}>{t.topic}: {t.band}</li>)}</ul></li>)}</ul>
        {data.not_started.length > 0 && <p className="mt-3 text-sm text-slate">Not started yet: {data.not_started.map((n) => n.name).join("; ")}.</p>}</section>
    </div>
  );
}

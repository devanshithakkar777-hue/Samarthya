"use client";

import Link from "next/link";
import { useMine } from "@/lib/useMine";
import { ErrorText } from "./kit/Controls";

type Rec = { kind: string; title: string; path: string; why: string; detail: string | null };
type D = { skill_gaps: { slug: string; name: string; needed_for: string[]; tiers: string[] }[]; recommendations: Rec[]; basis: string };

export default function ForYou() {
  const { data, error, loading } = useMine<D>("/v1/me/recommendations");
  if (loading) return <p role="status">Loading…</p>;
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return null;
  return (
    <div>
      <p className="mb-6 max-w-3xl rounded-md border border-ink/10 bg-white p-3 text-sm text-slate">{data.basis}</p>
      {data.recommendations.length === 0 ? (
        <p className="text-lg">Nothing to suggest yet. <Link className="text-electric-blue underline" href="/start">Add your degree and interests</Link>, save a role you like, or answer a few practice questions, and suggestions will appear here.</p>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">{data.recommendations.map((r, i) => (
          <li key={i} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-slate">{r.kind}</p>
            <h3 className="font-semibold"><Link className="text-electric-blue underline" href={r.path}>{r.title}</Link></h3>
            <p className="text-sm text-slate">{r.why}{r.detail ? ` · ${r.detail}` : ""}</p>
          </li>))}</ul>)}
      {data.skill_gaps.length > 0 && (<><h2 className="mb-3 mt-10 text-xl font-semibold">Skills to build for your saved roles</h2>
        <ul className="grid gap-2">{data.skill_gaps.map((g) => <li key={g.slug}><Link className="text-electric-blue underline" href={`/skills/${g.slug}`}>{g.name}</Link> <span className="text-sm text-slate">needed for {g.needed_for.join(", ")}</span></li>)}</ul></>)}
    </div>
  );
}

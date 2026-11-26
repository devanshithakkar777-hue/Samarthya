"use client";

import Link from "next/link";
import { useStudent } from "@/lib/student";
import { useMine } from "@/lib/useMine";

type M = { slug: string; title: string; organisation: string; reasons: string[]; to_check: string[]; blockers: string[] };
type D = { matches: M[]; worth_a_look: M[]; note: string };

export default function Matches() {
  const { user } = useStudent();
  const { data } = useMine<D>(user ? "/v1/me/opportunities/matches" : null);
  if (!user || !data) return null;
  if (data.matches.length === 0 && data.worth_a_look.length === 0) return (
    <p className="mb-8 rounded-md border border-ink/10 bg-white p-3 text-sm text-slate">Add your year of study and skills in <Link className="text-electric-blue underline" href="/start">your profile</Link> to see matches with reasons.</p>);
  return (
    <section aria-labelledby="m" className="mb-10"><h2 id="m" className="mb-2 text-xl font-semibold">Matched to what you told us</h2><p className="mb-3 text-sm text-slate">{data.note}</p>
      <ul className="grid gap-3 md:grid-cols-2">{[...data.matches, ...data.worth_a_look].map((o) => (
        <li key={o.slug} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4"><h3 className="font-semibold"><Link className="text-electric-blue underline" href={`/opportunities/${o.slug}`}>{o.title}</Link></h3><p className="text-sm text-slate">{o.organisation}</p>
          {o.reasons.length > 0 && <ul className="mt-2 list-disc pl-5 text-sm">{o.reasons.map((r) => <li key={r}>{r}</li>)}</ul>}
          {o.to_check.length > 0 && <p className="mt-1 text-sm text-slate">To check: {o.to_check.join("; ")}.</p>}
          {o.blockers.length > 0 && <p className="mt-1 text-sm"><strong>Check eligibility:</strong> {o.blockers.join("; ")}.</p>}</li>))}</ul></section>);
}

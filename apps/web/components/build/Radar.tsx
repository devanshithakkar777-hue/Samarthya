"use client";

import { useState } from "react";
import { useMine } from "@/lib/useMine";
import { inp, Note } from "@/components/kit/Controls";

type Role = { slug: string; title: string };
type D = { role: Role; tiers: { tier: string; total: number; done: number }[]; refresh: { label: string; tier: string }[]; note: string };
const NAME: Record<string, string> = { mandatory: "Must-haves", common_preference: "Commonly preferred", recommended: "Recommended", differentiator: "Stand-out extras" };

export default function Radar() {
  const roles = useMine<Role[]>("/v1/roles");
  const [slug, setSlug] = useState("");
  const d = useMine<D>(slug ? `/v1/me/radar/${slug}` : null);
  return (
    <section aria-labelledby="rd-h" className="mb-8 max-w-3xl grid gap-3">
      <h2 id="rd-h" className="text-2xl font-semibold">Career relevance radar</h2>
      <div><label htmlFor="rr" className="font-medium">Pick a role to check yourself against</label>
        <select id="rr" className={inp} value={slug} onChange={(e) => setSlug(e.target.value)}><option value="">Choose a role</option>{(roles.data ?? []).map((r) => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></div>
      {d.data && <><Note>{d.data.note}</Note>
        <ul className="grid gap-2 sm:grid-cols-2">{d.data.tiers.map((t) => <li key={t.tier} className="rounded-md border border-ink/10 bg-white p-3"><p className="font-medium">{NAME[t.tier] ?? t.tier}</p>
          <div className="mt-1 h-2 rounded bg-ice-blue/50" role="img" aria-label={`${t.done} of ${t.total} done`}><div className="h-2 rounded bg-electric-blue" style={{ width: `${t.total ? (t.done / t.total) * 100 : 0}%` }} /></div><p className="text-sm text-slate">{t.done} of {t.total} ticked</p></li>)}</ul>
        {d.data.refresh.length > 0 && <div><p className="font-medium">Worth checking again (ticked over a year ago)</p><ul className="list-disc pl-5 text-sm">{d.data.refresh.map((r, i) => <li key={i}>{r.label}</li>)}</ul></div>}</>}
    </section>
  );
}

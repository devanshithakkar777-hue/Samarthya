"use client";

import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useStudent } from "@/lib/student";
import type { Qualification, Roadmap } from "@/lib/types";
import { Empty, Source } from "./ui";

export default function RoadmapView({ quals }: { quals: Qualification[] }) {
  const { ready, profile } = useStudent();
  const [slug, setSlug] = useState("");
  const [data, setData] = useState<Roadmap | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => { if (ready && !slug && profile.qualification) setSlug(profile.qualification); }, [ready, profile.qualification, slug]);
  useEffect(() => {
    if (!slug) { setData(null); return; }
    let alive = true; setErr("");
    call<Roadmap>("GET", `/v1/roadmap?qualification=${encodeURIComponent(slug)}`).then((r) => alive && setData(r)).catch((e: Error) => alive && (setErr(e.message), setData(null)));
    return () => { alive = false; };
  }, [slug]);

  return (
    <div>
      <label htmlFor="rq" className="font-semibold">Your degree</label>
      <select id="rq" value={slug} onChange={(e) => setSlug(e.target.value)} className="mt-1 block w-full max-w-md rounded-md border border-slate/50 bg-white px-3 py-3">
        <option value="">Choose a degree</option>
        {quals.map((q) => (<option key={q.id} value={q.slug}>{q.degree}{q.specialization ? `, ${q.specialization}` : ""}</option>))}
      </select>
      {err && <p role="alert" className="mt-4 rounded bg-ink p-3 text-arctic-white">{err}</p>}
      {data && (data.years.length ? (
        <ol className="mt-8 grid gap-6">
          {data.years.map((y) => (
            <li key={y.year} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
              <h3 className="text-xl font-semibold">Year {y.year}</h3>
              <ul className="mt-3 grid gap-4">
                {y.steps.map((s) => (<li key={s.id}><p className="font-medium">{s.title}</p><p className="text-slate">{s.detail}</p><Source p={s} /></li>))}
              </ul>
            </li>
          ))}
        </ol>
      ) : <div className="mt-8"><Empty title="No roadmap steps are published for this degree yet" /></div>)}
    </div>
  );
}

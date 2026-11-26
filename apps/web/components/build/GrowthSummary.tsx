"use client";

import { useMine } from "@/lib/useMine";
import { Note } from "@/components/kit/Controls";

type D = { counts: Record<string, number>; by_month: Record<string, number>; checklist: { item: string; done: boolean }[]; note: string };
export default function GrowthSummary() {
  const { data } = useMine<D>("/v1/me/growth-summary");
  if (!data) return null;
  const months = Object.entries(data.by_month);
  const max = Math.max(1, ...months.map(([, v]) => v));
  return (
    <section aria-labelledby="gs-h" className="mb-8 grid max-w-3xl gap-4">
      <h2 id="gs-h" className="text-2xl font-semibold">Promotion readiness record</h2>
      <Note>{data.note}</Note>
      <ul className="grid gap-2">{data.checklist.map((c) => <li key={c.item} className="flex items-center gap-2 rounded-md border border-ink/10 bg-white p-3"><span aria-hidden="true">{c.done ? "✓" : "○"}</span><span>{c.item}</span><span className="sr-only">{c.done ? "done" : "not yet"}</span></li>)}</ul>
      {months.length > 0 && <div><p className="mb-1 text-sm text-slate">Entries added per month</p>
        <ul className="flex items-end gap-2" aria-label="Entries per month">{months.map(([k, v]) => <li key={k} className="text-center text-xs"><div className="mx-auto w-6 rounded-t bg-electric-blue" style={{ height: `${(v / max) * 60 + 4}px` }} title={`${k}: ${v}`} /><span>{k.slice(5)}</span><span className="sr-only"> {v} entries</span></li>)}</ul></div>}
    </section>
  );
}

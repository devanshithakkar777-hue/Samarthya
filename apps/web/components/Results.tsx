"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useStudent } from "@/lib/student";
import type { FitItem } from "@/lib/types";
import { Empty, Source, btn } from "./ui";

type Sort = "eligibility" | "compatibility" | "readiness";
const WORDS: Record<string, string> = {
  eligible: "Your degree is listed", open: "Open to many degrees", unknown: "We could not confirm", not_listed: "Your degree is not listed",
  strong: "Strong match", partial: "Partial match", low: "Weak match",
  close: "Close", some_preparation: "Some preparation needed", substantial_preparation: "Substantial preparation needed", no_requirements_listed: "No requirements listed yet",
  pages_listed: "Hiring pages listed", none_listed: "No hiring pages listed yet",
};
const w = (l: string) => WORDS[l] ?? l.replace(/_/g, " ");

function Answer({ title, label, reasons }: { title: string; label: string; reasons: string[] }) {
  return (
    <div>
      <h4 className="text-sm font-medium text-slate">{title}</h4>
      <p className="font-semibold">{w(label)}</p>
      {reasons.length > 0 && <ul className="mt-1 list-disc pl-5 text-sm text-slate">{reasons.map((r, i) => (<li key={i}>{r}</li>))}</ul>}
    </div>
  );
}

export default function Results() {
  const { ready, hasProfile, loadFit, completed } = useStudent();
  const [sort, setSort] = useState<Sort>("eligibility");
  const [items, setItems] = useState<FitItem[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!ready || !hasProfile) return;
    let alive = true;
    setErr("");
    loadFit(sort).then((r) => alive && setItems(r)).catch((e: Error) => alive && setErr(e.message));
    return () => { alive = false; };
  }, [ready, hasProfile, sort, completed, loadFit]);

  if (!ready) return <p role="status">Loading…</p>;
  if (!hasProfile) return (
    <Empty title="Tell us a little about you first"><Link href="/start" className={`${btn} mt-4`}>Find my path</Link></Empty>
  );
  if (err) return <p role="alert" className="rounded bg-ink p-4 text-arctic-white">{err}</p>;
  if (!items) return <p role="status">Working out your options…</p>;
  if (!items.length) return <Empty title="No careers are published yet">We publish a career only after it is checked against a source. Please check back soon.</Empty>;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <label htmlFor="sort" className="font-medium">Order by</label>
        <select id="sort" value={sort} onChange={(e) => setSort(e.target.value as Sort)} className="rounded-md border border-slate/50 bg-white px-3 py-2">
          <option value="eligibility">Degree listed first</option>
          <option value="compatibility">Interest match first</option>
          <option value="readiness">Closest to ready first</option>
        </select>
        <Link href="/start" className="ml-auto text-electric-blue underline">Change my answers</Link>
      </div>
      <ul className="grid gap-5">
        {items.map((it) => (
          <li key={it.role.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-xl font-semibold"><Link className="hover:text-electric-blue" href={`/roles/${it.role.slug}`}>{it.role.title}</Link></h3>
              <span className="text-sm text-slate">{it.role.sector.name} · {it.role.level}</span>
            </div>
            <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <Answer title="Does your degree qualify?" label={it.eligibility.label} reasons={it.eligibility.reasons} />
              <Answer title="Does it suit your interests?" label={it.compatibility.label} reasons={it.compatibility.reasons} />
              <Answer title="How ready are you?" label={it.readiness.label} reasons={it.readiness.reasons} />
              <div>
                <Answer title="Where can you look?" label={it.opportunity.label} reasons={[]} />
                <ul className="mt-1 text-sm">
                  {it.opportunity.hiring_pages.slice(0, 3).map((h) => (
                    <li key={h.company_slug}><a className="text-electric-blue underline" href={h.careers_url} target="_blank" rel="noopener noreferrer">{h.company}<span className="sr-only"> (opens in a new tab)</span></a></li>
                  ))}
                </ul>
              </div>
            </div>
            {it.readiness.outstanding.length > 0 && (
              <p className="mt-4 text-sm"><Link className="text-electric-blue underline" href={`/roles/${it.role.slug}`}>See your checklist: {it.readiness.outstanding.length} {it.readiness.outstanding.length === 1 ? "item" : "items"} left</Link></p>
            )}
            <Source p={it.role} />
          </li>
        ))}
      </ul>
    </div>
  );
}

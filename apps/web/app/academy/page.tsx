import type { Metadata } from "next";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { Card, Empty, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Academy" };
type L = { slug: string; pillar: string; track: string; title: string; summary: string; level: string; minutes: number | null; language: string };
type Res = { results: L[]; tracks: Record<string, Record<string, number>>; pillars: Record<string, string> };

export default async function Page({ searchParams }: { searchParams: Promise<{ pillar?: string; q?: string; level?: string }> }) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  for (const k of ["pillar", "q", "level"] as const) if (sp[k]) qs.set(k, sp[k]!);
  const data = await apiGet<Res>(`/v1/lessons${qs.size ? `?${qs}` : ""}`, 60);
  const byTrack = new Map<string, L[]>();
  for (const l of data.results) byTrack.set(`${data.pillars[l.pillar] ?? l.pillar}: ${l.track}`, [...(byTrack.get(`${data.pillars[l.pillar] ?? l.pillar}: ${l.track}`) ?? []), l]);
  return (
    <>
      <PageHead title="Academy" lead="Short lessons on thinking, money, communication, AI at work and life skills. Each one shows its source and when it was last checked." crumbs={[{ href: "/learn", label: "Learn" }]} />
      <Section>
        <form className="mb-6 flex flex-wrap items-end gap-3" role="search" aria-label="Search lessons">
          <div><label htmlFor="q" className="block font-medium">Search</label><input id="q" name="q" defaultValue={sp.q} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2" /></div>
          <div><label htmlFor="pillar" className="block font-medium">Area</label>
            <select id="pillar" name="pillar" defaultValue={sp.pillar ?? ""} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2">
              <option value="">All areas</option>{Object.entries(data.pillars).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></div>
          <div><label htmlFor="level" className="block font-medium">Level</label>
            <select id="level" name="level" defaultValue={sp.level ?? ""} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2">
              <option value="">Any</option><option>beginner</option><option>intermediate</option><option>advanced</option></select></div>
          <button className="rounded-md bg-electric-blue px-5 py-2 font-medium text-arctic-white">Filter</button>
        </form>
        {data.results.length === 0 ? (
          <Empty title="No lessons published yet">Lessons appear here only after they have been written from a cited source and checked by a second person. <Link className="text-electric-blue underline" href="/explore">Browse careers</Link> meanwhile.</Empty>
        ) : [...byTrack.entries()].map(([track, ls]) => (
          <div key={track} className="mb-8"><h2 className="mb-3 text-xl font-semibold">{track}</h2>
            <ul className="grid gap-4 md:grid-cols-3">{ls.map((l) => <li key={l.slug}><Card href={`/academy/${l.slug}`} title={l.title}>{l.summary}<br /><span className="text-xs">{l.level}{l.minutes ? ` · ${l.minutes} min` : ""} · {l.language}</span></Card></li>)}</ul></div>
        ))}
      </Section>
    </>
  );
}

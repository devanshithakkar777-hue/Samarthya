import type { Metadata } from "next";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import Matches from "@/components/explore/Matches";
import { Card, Empty, fmtDate, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Opportunities" };
type O = { slug: string; title: string; organisation: string; kind: string; location: string | null; mode: string | null; stipend: string | null; deadline: string | null; rolling: boolean };
type R = { results: O[]; kinds: Record<string, number> };

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  for (const k of ["kind", "mode", "q", "location", "year"]) if (sp[k]) qs.set(k, sp[k]!);
  const d = await apiGet<R>(`/v1/opportunities${qs.size ? `?${qs}` : ""}`, 30);
  return (<><PageHead title="Opportunities" lead="Internships, scholarships, fellowships, competitions and more. Every listing links to the organiser's own page, and closed ones disappear." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section>
      <Matches />
      <form role="search" aria-label="Filter opportunities" className="mb-6 flex flex-wrap items-end gap-3">
        <div><label htmlFor="q" className="block font-medium">Search</label><input id="q" name="q" defaultValue={sp.q} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2" /></div>
        <div><label htmlFor="kind" className="block font-medium">Kind</label><select id="kind" name="kind" defaultValue={sp.kind ?? ""} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2"><option value="">All</option>{Object.keys(d.kinds).map((k) => <option key={k}>{k}</option>)}</select></div>
        <div><label htmlFor="mode" className="block font-medium">Mode</label><select id="mode" name="mode" defaultValue={sp.mode ?? ""} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2"><option value="">Any</option><option>remote</option><option>onsite</option><option>hybrid</option></select></div>
        <button className="rounded-md bg-electric-blue px-5 py-2 font-medium text-arctic-white">Filter</button>
      </form>
      {d.results.length === 0 ? <Empty title="No open opportunities published right now">Each one is added only after we have opened the organiser&apos;s page. <Link className="text-electric-blue underline" href="/report">Tell us about one</Link>.</Empty> : (
        <ul className="grid gap-4 md:grid-cols-2">{d.results.map((o) => <li key={o.slug}><Card href={`/opportunities/${o.slug}`} title={o.title}>{o.organisation} · {o.kind}<br /><span className="text-xs">{[o.location, o.mode, o.stipend, o.rolling ? "Rolling applications" : o.deadline ? `Apply by ${fmtDate(o.deadline)}` : null].filter(Boolean).join(" · ")}</span></Card></li>)}</ul>)}
    </Section></>);
}

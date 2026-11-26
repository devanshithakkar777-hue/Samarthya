import type { Metadata } from "next";
import Link from "next/link";
import WorldMap from "@/components/world/WorldMap";
import { apiGet } from "@/lib/api";
import { Card, Empty, fmtDate, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "World and global awareness" };
type B = { slug: string; category: string; region: string | null; event_date: string; headline: string };
type C = { slug: string; name: string; iso_numeric: string; region: string | null };
type T = { slug: string; year: number; title: string; summary: string; region: string | null; category: string | null };

export default async function Page({ searchParams }: { searchParams: Promise<{ category?: string }> }) {
  const sp = await searchParams;
  const [b, c, t] = await Promise.all([
    apiGet<{ results: B[]; categories: Record<string, number> }>(`/v1/briefs${sp.category ? `?category=${encodeURIComponent(sp.category)}` : ""}`),
    apiGet<{ results: C[] }>("/v1/countries"), apiGet<{ results: T[] }>("/v1/timeline"),
  ]);
  return (<><PageHead title="World and global awareness" lead="Events, countries and history explained step by step: what happened, why, who is affected and what to look into next. Written neutrally from cited sources." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section title="Countries"><WorldMap countries={c.results} />
      {c.results.length > 0 && <ul className="mt-4 flex flex-wrap gap-2">{c.results.map((x) => <li key={x.slug}><Link className="rounded-md border border-ink/20 bg-white px-3 py-1 text-sm text-electric-blue underline" href={`/world/countries/${x.slug}`}>{x.name}</Link></li>)}</ul>}</Section>
    <Section title="Briefs">
      <p className="mb-3"><Link className="text-electric-blue underline" href="/world/map">Connect the dots: see how briefs link</Link> · <Link className="text-electric-blue underline" href="/world/daily">Daily briefing</Link> · <Link className="text-electric-blue underline" href="/practise/cases?pillar=thinker">Global Thinker Challenge</Link> · <Link className="text-electric-blue underline" href="/world/timeline">History explorer</Link></p>
      <nav aria-label="Brief categories" className="mb-4 flex flex-wrap gap-2"><Link className="rounded-md border border-ink/20 bg-white px-3 py-1 text-sm" href="/world">All</Link>
        {Object.keys(b.categories).map((k) => <Link key={k} className="rounded-md border border-ink/20 bg-white px-3 py-1 text-sm" href={`/world?category=${encodeURIComponent(k)}`}>{k} ({b.categories[k]})</Link>)}</nav>
      {b.results.length === 0 ? <Empty title="No briefs published yet">Each brief is written from cited sources and checked by a second person before it appears.</Empty> : (
        <ul className="grid gap-4 md:grid-cols-2">{b.results.map((x) => <li key={x.slug}><Card href={`/world/briefs/${x.slug}`} title={x.headline}>{x.category}{x.region ? ` · ${x.region}` : ""} · {fmtDate(x.event_date)}</Card></li>)}</ul>)}</Section>
    <Section title="Timeline">
      {t.results.length === 0 ? <p className="text-slate">No timeline events published yet.</p> : (
        <ol className="grid gap-3 border-l-2 border-electric-blue pl-5">{t.results.map((e) => <li key={e.slug}><p className="text-sm font-semibold text-electric-blue">{e.year < 0 ? `${-e.year} BCE` : e.year}</p><h3 className="font-semibold">{e.title}</h3><p className="text-sm text-slate">{e.summary}</p></li>)}</ol>)}</Section></>);
}

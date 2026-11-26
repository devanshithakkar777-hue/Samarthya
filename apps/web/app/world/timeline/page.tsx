import type { Metadata } from "next";
import Link from "next/link";
import { apiTry } from "@/lib/api";
import { Empty, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "History explorer" };
type E = { slug: string; year: number; title: string; summary: string; region?: string; category?: string; provenance?: { source_url?: string; last_verified?: string } };

export default async function Page({ searchParams }: { searchParams: Promise<{ region?: string; category?: string }> }) {
  const sp = await searchParams;
  const qs = new URLSearchParams(Object.entries(sp).filter(([, v]) => v) as [string, string][]).toString();
  const d = await apiTry<{ results: E[] }>(`/v1/timeline${qs ? `?${qs}` : ""}`, { results: [] }, 120);
  const regions = [...new Set(d.results.map((e) => e.region).filter(Boolean))] as string[];
  const label = (y: number) => (y < 0 ? `${-y} BCE` : String(y));
  return (<><PageHead title="History explorer" lead="Events in order, each with a source. Use it to see what led to what, then read the matching world briefs." crumbs={[{ href: "/world", label: "World" }]} />
    <Section>{d.results.length === 0 ? <Empty title="No events published yet">Timeline events appear after an editor adds a source and a reviewer approves them.</Empty> : <>
      {regions.length > 0 && <nav aria-label="Regions" className="mb-4 flex flex-wrap gap-2"><Link className="rounded-md border border-ink/20 bg-white px-3 py-1 text-sm" href="/world/timeline">All regions</Link>
        {regions.map((r) => <Link key={r} className="rounded-md border border-ink/20 bg-white px-3 py-1 text-sm" href={`/world/timeline?region=${encodeURIComponent(r)}`}>{r}</Link>)}</nav>}
      <ol className="grid max-w-3xl gap-3 border-l-2 border-electric-blue pl-5">{d.results.map((e) => <li key={e.slug}><p className="font-semibold">{label(e.year)}: {e.title}</p><p>{e.summary}</p>
        <p className="text-sm text-slate">{[e.region, e.category].filter(Boolean).join(" · ")}{e.provenance?.source_url && <> · <a className="text-electric-blue underline" href={e.provenance.source_url} rel="noopener noreferrer">Source</a></>}{e.provenance?.last_verified && ` · checked ${e.provenance.last_verified}`}</p></li>)}</ol></>}</Section></>);
}

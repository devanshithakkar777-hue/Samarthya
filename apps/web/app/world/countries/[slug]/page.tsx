import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { PageHead, Section, Source } from "@/components/ui";

type C = { name: string; region: string | null; capital: string | null; summary: string; facts: Record<string, string> | null; provenance: Provenance; timeline: { year: number; title: string; summary: string }[] };
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { return { title: (await apiGet<C>(`/v1/countries/${(await params).slug}`)).name }; }
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const c = await apiGet<C>(`/v1/countries/${(await params).slug}`);
  return (<><PageHead title={c.name} lead={[c.region, c.capital ? `Capital: ${c.capital}` : null].filter(Boolean).join(" · ")} crumbs={[{ href: "/explore", label: "Explore" }, { href: "/world", label: "World" }]} />
    <Section><div className="max-w-3xl"><p className="whitespace-pre-line text-lg">{c.summary}</p>
      {c.facts && Object.keys(c.facts).length > 0 && <dl className="mt-6 grid gap-x-8 gap-y-2 sm:grid-cols-2">{Object.entries(c.facts).map(([k, v]) => <div key={k}><dt className="text-sm text-slate">{k}</dt><dd>{String(v)}</dd></div>)}</dl>}
      <Source p={c.provenance} />
      {c.timeline.length > 0 && <><h2 className="mb-3 mt-8 text-xl font-semibold">Timeline</h2><ol className="grid gap-3 border-l-2 border-electric-blue pl-5">{c.timeline.map((e, i) => <li key={i}><p className="text-sm font-semibold text-electric-blue">{e.year < 0 ? `${-e.year} BCE` : e.year}</p><h3 className="font-semibold">{e.title}</h3><p className="text-sm text-slate">{e.summary}</p></li>)}</ol></>}</div></Section></>);
}

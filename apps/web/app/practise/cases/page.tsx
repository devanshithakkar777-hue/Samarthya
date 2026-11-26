import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import { Card, Empty, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Cases and challenges" };
type S = { slug: string; title: string; pillar: string; pillar_label: string; difficulty: number; minutes: number | null; kind_note: string };

export default async function Page({ searchParams }: { searchParams: Promise<{ pillar?: string }> }) {
  const { pillar } = await searchParams;
  const d = await apiGet<{ results: S[] }>(`/v1/scenarios${pillar ? `?pillar=${encodeURIComponent(pillar)}` : ""}`);
  const title = pillar === "thinker" ? "Global Thinker Challenge" : pillar === "conflict" ? "Team conflict simulator" : "Cases and challenges";
  return (<><PageHead title={title} lead="Decide what you would do, see what follows, then read the debrief. Real cases cite their public source; constructed ones say so." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section>{d.results.length === 0 ? <Empty title="No cases published yet">Cases are written from public sources and reviewed before they appear.</Empty> : (
      <ul className="grid gap-4 md:grid-cols-3">{d.results.map((s) => <li key={s.slug}><Card href={`/practise/cases/${s.slug}`} title={s.title}>{s.pillar_label}<br /><span className="text-xs">{s.kind_note}{s.minutes ? ` · about ${s.minutes} min` : ""}</span></Card></li>)}</ul>)}</Section></>);
}

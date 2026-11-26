import type { Metadata } from "next";
import Link from "next/link";
import { apiTry } from "@/lib/api";
import { Empty, fmtDate, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Daily world briefing" };
type B = { slug: string; category: string; region: string | null; event_date: string; headline: string };

export default async function Page() {
  const d = await apiTry<{ results: B[] }>("/v1/briefs", { results: [] }, 300);
  const byDay = new Map<string, B[]>();
  for (const b of d.results.slice(0, 60)) byDay.set(b.event_date, [...(byDay.get(b.event_date) ?? []), b]);
  return (<><PageHead title="Daily world briefing" lead="The most recent events, newest first. Each brief explains what happened, why it matters and what to look into next, from cited sources." crumbs={[{ href: "/world", label: "World" }]} />
    <Section>{byDay.size === 0 ? <Empty title="No briefs published yet">A brief appears only after it has been sourced and checked by a second person.</Empty> : (
      <div className="grid gap-6">{Array.from(byDay).map(([day, list]) => (
        <section key={day} aria-labelledby={`d-${day}`}><h2 id={`d-${day}`} className="text-xl font-semibold">{fmtDate(day)}</h2>
          <ul className="mt-2 grid gap-2">{list.map((b) => <li key={b.slug}><Link className="text-electric-blue underline" href={`/world/briefs/${b.slug}`}>{b.headline}</Link> <span className="text-sm text-slate">{b.category}{b.region ? ` · ${b.region}` : ""}</span></li>)}</ul></section>))}</div>)}</Section></>);
}

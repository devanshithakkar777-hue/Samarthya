import type { Metadata } from "next";
import CrisisBox from "@/components/live/CrisisBox";
import Journal from "@/components/live/Journal";
import Private from "@/components/kit/Private";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { PageHead, Section, Source } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Wellbeing" };
type Crisis = { resources: React.ComponentProps<typeof CrisisBox>["c"]["resources"]; checked_on: string; note: string };
type W = { slug: string; title: string; kind: string; summary: string; phone: string | null; url: string | null; hours: string | null; languages: string[] | null; cost: string | null; audience: string | null; provenance: Provenance };

export default async function Page() {
  const [c, w] = await Promise.all([apiGet<Crisis>("/v1/crisis", 300), apiGet<{ results: W[] }>("/v1/wellness/resources", 300)]);
  return (<><PageHead title="Wellbeing" lead="Stress, loneliness and pressure are common, and help exists. This page is support and information. It is not therapy and it cannot diagnose anything." crumbs={[{ href: "/live", label: "Live" }]} />
    <Section><CrisisBox c={{ message: "", resources: c.resources }} checkedOn={c.checked_on} /></Section>
    <Section title="More support">
      {w.results.length === 0 ? <p className="text-slate">More resources will appear here after they have been checked. The numbers above are always available.</p> : (
        <ul className="grid gap-4 md:grid-cols-2">{w.results.map((r) => <li key={r.slug} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5"><h3 className="font-semibold">{r.title}</h3><p className="text-sm text-slate">{r.kind}{r.hours ? ` · ${r.hours}` : ""}{r.cost ? ` · ${r.cost}` : ""}</p><p className="mt-1">{r.summary}</p>
          {r.phone && <p className="mt-1"><a className="text-electric-blue underline" href={`tel:${r.phone.replace(/[^\d+]/g, "")}`}>{r.phone}</a></p>}{r.url && <p><a className="text-electric-blue underline" href={r.url} target="_blank" rel="noopener noreferrer">Official page<span className="sr-only"> (opens in a new tab)</span></a></p>}<Source p={r.provenance} /></li>)}</ul>)}</Section>
    <Section title="Your private journal">
      <p className="mb-4 max-w-3xl text-slate">Writing things down can help you notice how you are doing. What you write here is encrypted, belongs only to you, and is never shared with your institution or any employer. It is never counted, scored or ranked.</p>
      <Private why="Your journal is private to you, so it needs an account."><Journal /></Private></Section></>);
}

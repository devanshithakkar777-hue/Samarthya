import type { Metadata } from "next";
import Link from "next/link";
import { Card, PageHead, Section, Source } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { FIELD_LABEL, KIND_LABEL, KIND_NOTE } from "@/lib/pathways";
import type { PathwayDetail } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;
type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  try { return { title: (await apiGet<PathwayDetail>(`/v1/pathways/${slug}`)).name }; } catch { return { title: "Qualification" }; }
}

export default async function PathwayPage({ params }: P) {
  const { slug } = await params;
  const d = await apiGet<PathwayDetail>(`/v1/pathways/${slug}`);
  const held: [string, string | null][] = [
    ["Type of qualification", KIND_LABEL[d.kind] ?? d.kind],
    ["Stream", d.stream],
    ["Level", d.level === "unspecified" ? null : d.level],
    ["Awarding authority", d.awarding_body],
    ["Duration", d.duration_years != null ? `${d.duration_years} ${d.duration_years === 1 ? "year" : "years"}` : null],
  ];
  return (
    <>
      <PageHead title={d.name} lead={KIND_NOTE[d.kind]} crumbs={[{ href: "/pathways", label: "Education and qualifications" }]} />
      <Section title="What we know">
        <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
          {held.map(([k, v]) => (
            <div key={k}><dt className="text-sm font-medium text-slate">{k}</dt><dd>{v ?? <span className="text-slate">Not yet verified</span>}</dd></div>))}
        </dl>
        <Source p={d} />
      </Section>
      {([["eligibility", d.eligibility], ["entry_route", d.entry_route], ["training", d.training], ["recognition", d.recognition], ["cost_note", d.cost_note]] as [string, string | null][])
        .filter(([, v]) => v).map(([k, v]) => (
          <Section key={k} title={FIELD_LABEL[k]}><p className="max-w-3xl whitespace-pre-line">{v}</p></Section>))}
      {d.official_url && (
        <Section title="Official link">
          <a className="text-electric-blue underline break-all" href={d.official_url} target="_blank" rel="noopener noreferrer">{d.official_url}<span className="sr-only"> (opens in a new tab)</span></a>
          <p className="mt-2 text-sm text-slate">Rules change. Confirm the current requirements on the official page before you plan around them.</p>
        </Section>)}
      <Section title="Not yet verified">
        <p className="text-slate">We do not guess these. Check the awarding body&apos;s own pages until we have reviewed them against a source.</p>
        <ul className="mt-3 list-disc pl-6">
          {d.not_yet_verified.map((f) => (<li key={f}>{FIELD_LABEL[f] ?? f}</li>))}
        </ul>
      </Section>
      <Section title="Where it can lead">
        {d.sectors.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {d.sectors.map((s) => (<Card key={s.slug} href={`/explore/${s.slug}`} title={s.name}><p>{s.reason}</p></Card>))}
          </div>
        ) : <p className="text-slate">Sectors for this qualification have not been published yet.</p>}
        {d.roles.length > 0 && (
          <ul className="mt-4 flex flex-wrap gap-2">
            {d.roles.map((r) => (<li key={r.slug}><Link className="rounded-full border border-ink/20 px-3 py-1.5 text-sm hover:border-electric-blue" href={`/roles/${r.slug}`}>{r.title}</Link></li>))}
          </ul>)}
      </Section>
    </>
  );
}

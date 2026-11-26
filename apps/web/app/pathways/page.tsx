import type { Metadata } from "next";
import Link from "next/link";
import { Card, Empty, PageHead, Section, btn } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { KIND_LABEL, STAGES } from "@/lib/pathways";
import type { PathwayList } from "@/lib/types";

export const metadata: Metadata = { title: "Education and qualification explorer" };
export const dynamic = "force-dynamic";
type SP = { searchParams: Promise<{ stage?: string; stream?: string; kind?: string; q?: string }> };

function href(cur: Record<string, string | undefined>, patch: Record<string, string | undefined>) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries({ ...cur, ...patch })) if (v) p.set(k, v);
  const s = p.toString();
  return s ? `/pathways?${s}` : "/pathways";
}

export default async function Pathways({ searchParams }: SP) {
  const sp = await searchParams;
  const cur = { stage: sp.stage, stream: sp.stream, kind: sp.kind, q: sp.q?.slice(0, 80) };
  const qs = new URLSearchParams(Object.entries(cur).filter(([, v]) => v) as [string, string][]).toString();
  const data = await apiGet<PathwayList>(`/v1/pathways${qs ? `?${qs}` : ""}`, 30);
  const anyFilter = Object.values(cur).some(Boolean);
  const chip = (on: boolean) => `rounded-full border px-3 py-1.5 text-sm ${on ? "border-electric-blue bg-electric-blue text-arctic-white" : "border-ink/20 bg-white text-ink hover:border-electric-blue"}`;
  return (
    <>
      <PageHead title="Education and qualification explorer" lead="Every route to learning and professional qualification in one place, with degrees, diplomas, professional qualifications and certifications kept clearly apart." />
      <Section>
        <form action="/pathways" method="get" role="search" className="mb-6 flex flex-wrap items-end gap-3">
          {cur.stage && <input type="hidden" name="stage" value={cur.stage} />}
          {cur.stream && <input type="hidden" name="stream" value={cur.stream} />}
          {cur.kind && <input type="hidden" name="kind" value={cur.kind} />}
          <label className="grow text-sm font-medium" htmlFor="q">Search by name or abbreviation
            <input id="q" name="q" defaultValue={cur.q ?? ""} maxLength={80} className="mt-1 block w-full rounded-md border border-ink/30 px-3 py-2 font-normal" placeholder="for example CA, B.Des, ITI" />
          </label>
          <button className={btn}>Search</button>
        </form>

        <h2 className="text-lg font-semibold">1. Where are you in your education?</h2>
        <p className="mt-1 text-sm text-slate">A starting filter only. Always confirm eligibility with the awarding body.</p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {STAGES.map((s) => (<li key={s.id}><Link className={chip(cur.stage === s.id)} aria-current={cur.stage === s.id ? "true" : undefined} href={href(cur, { stage: cur.stage === s.id ? undefined : s.id })}>{s.label}</Link></li>))}
        </ul>

        <h2 className="mt-8 text-lg font-semibold">2. Choose a stream</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {Object.entries(data.streams).map(([name, n]) => (
            <li key={name}><Link className={chip(cur.stream === name)} aria-current={cur.stream === name ? "true" : undefined} href={href(cur, { stream: cur.stream === name ? undefined : name })}>{name} ({n})</Link></li>))}
        </ul>

        <h2 className="mt-8 text-lg font-semibold">3. What type of qualification?</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {Object.entries(data.kinds).map(([k, n]) => (
            <li key={k}><Link className={chip(cur.kind === k)} aria-current={cur.kind === k ? "true" : undefined} href={href(cur, { kind: cur.kind === k ? undefined : k })}>{KIND_LABEL[k] ?? k} ({n})</Link></li>))}
        </ul>
        <p className="mt-4 text-sm text-slate">These types are not equivalent. A professional qualification or certification is not the same as an accredited university degree.</p>
      </Section>

      <Section title={`${data.total}${data.truncated ? "+" : ""} ${data.total === 1 ? "result" : "results"}`}>
        {anyFilter && <p className="mb-4"><Link className="text-electric-blue underline" href="/pathways">Clear all filters</Link></p>}
        {data.items.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((i) => (
              <Card key={i.slug} href={`/pathways/${i.slug}`} title={i.name}>
                <p>{KIND_LABEL[i.kind] ?? i.kind}{i.stream ? ` · ${i.stream}` : ""}</p>
                {i.awarding_body && <p>Awarded by {i.awarding_body}</p>}
                {i.duration_years != null && <p>{i.duration_years} {i.duration_years === 1 ? "year" : "years"}</p>}
              </Card>))}
          </div>
        ) : anyFilter ? (
          <Empty title="Nothing matches these filters">Try removing a filter. We only list qualifications after they have been reviewed against a source.</Empty>
        ) : (
          <Empty title="No qualifications are published yet">We only publish a qualification after its facts are reviewed against a source. Please check back soon.</Empty>
        )}
        {data.truncated && <p className="mt-4 text-sm text-slate">Showing the first 300. Narrow the search to see the rest.</p>}
      </Section>
    </>
  );
}

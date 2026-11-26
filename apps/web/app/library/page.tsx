import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { Empty, PageHead, Section, Source } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Library" };
type I = { slug: string; title: string; authors: string | null; kind: string; subject: string; language: string | null; publisher: string | null; access_url: string; format: string | null; level: string | null; licence: { label: string; note: string | null }; provenance: Provenance };
type R = { results: I[]; facets: Record<string, Record<string, number>>; policy: string };

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const qs = new URLSearchParams();
  for (const k of ["q", "kind", "subject", "language"]) if (sp[k]) qs.set(k, sp[k]!);
  const d = await apiGet<R>(`/v1/library${qs.size ? `?${qs}` : ""}`, 60);
  return (
    <>
      <PageHead title="Library" lead="Readings and study material you can use legally and for free. We link to them; we never copy or host books." crumbs={[{ href: "/learn", label: "Learn" }]} />
      <Section>
        <p className="mb-6 max-w-3xl rounded-md border border-ink/10 bg-white p-4 text-sm text-slate">{d.policy}</p>
        <form role="search" aria-label="Search the library" className="mb-6 flex flex-wrap items-end gap-3">
          <div><label htmlFor="q" className="block font-medium">Search</label><input id="q" name="q" defaultValue={sp.q} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2" /></div>
          {(["kind", "subject", "language"] as const).map((f) => (
            <div key={f}><label htmlFor={f} className="block font-medium capitalize">{f}</label>
              <select id={f} name={f} defaultValue={sp[f] ?? ""} className="mt-1 rounded-md border border-slate/50 bg-white px-3 py-2"><option value="">All</option>{Object.keys(d.facets[f] ?? {}).map((o) => <option key={o}>{o}</option>)}</select></div>
          ))}
          <button className="rounded-md bg-electric-blue px-5 py-2 font-medium text-arctic-white">Filter</button>
        </form>
        {d.results.length === 0 ? <Empty title="Nothing here yet">Items are added only when we can show the legal basis for linking to them.</Empty> : (
          <ul className="grid gap-4">{d.results.map((i) => (
            <li key={i.slug} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
              <h2 className="text-lg font-semibold"><a className="text-electric-blue underline" href={i.access_url} target="_blank" rel="noopener noreferrer">{i.title}<span className="sr-only"> (opens in a new tab)</span></a></h2>
              <p className="text-sm text-slate">{[i.authors, i.publisher, i.kind, i.subject, i.language].filter(Boolean).join(" · ")}</p>
              <p className="mt-2 text-sm"><strong>Why you may read it free:</strong> {i.licence.label}{i.licence.note ? `. ${i.licence.note}` : ""}</p>
              <Source p={i.provenance} />
            </li>))}</ul>)}
      </Section>
    </>
  );
}

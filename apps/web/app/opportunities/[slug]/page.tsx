import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import TrackButton from "@/components/explore/TrackButton";
import { fmtDate, PageHead, Section, Source } from "@/components/ui";

type O = { slug: string; title: string; organisation: string; kind: string; location: string | null; mode: string | null; stipend: string | null; duration: string | null; deadline: string | null; rolling: boolean; expired: boolean;
  description: string; eligibility: string; streams: string[]; skills: string[]; selection_process: string | null; apply_url: string; min_year: number | null; max_year: number | null; provenance: Provenance };
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { return { title: (await apiGet<O>(`/v1/opportunities/${(await params).slug}`)).title }; }

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const o = await apiGet<O>(`/v1/opportunities/${(await params).slug}`, 30);
  const rows: [string, string | null][] = [["Organisation", o.organisation], ["Kind", o.kind], ["Where", [o.location, o.mode].filter(Boolean).join(", ") || null], ["Stipend or value", o.stipend], ["Duration", o.duration],
    ["Deadline", o.rolling ? "Rolling applications" : o.deadline ? fmtDate(o.deadline) : null], ["Years of study", o.min_year || o.max_year ? `${o.min_year ?? 1} to ${o.max_year ?? "any"}` : null], ["Streams", o.streams?.join(", ") || null]];
  return (<><PageHead title={o.title} lead={o.organisation} crumbs={[{ href: "/explore", label: "Explore" }, { href: "/opportunities", label: "Opportunities" }]} />
    <Section><div className="max-w-3xl">
      {o.expired && <p role="status" className="mb-4 rounded bg-ink p-3 text-arctic-white">This opportunity has closed. Check the organiser&apos;s page for the next round.</p>}
      <dl className="grid gap-x-8 gap-y-2 sm:grid-cols-2">{rows.filter(([, v]) => v).map(([k, v]) => <div key={k}><dt className="text-sm text-slate">{k}</dt><dd>{v}</dd></div>)}</dl>
      <h2 className="mt-8 text-xl font-semibold">About</h2><p className="mt-2 whitespace-pre-line">{o.description}</p>
      <h2 className="mt-6 text-xl font-semibold">Who can apply</h2><p className="mt-2 whitespace-pre-line">{o.eligibility}</p>
      {o.selection_process && <><h2 className="mt-6 text-xl font-semibold">How selection works</h2><p className="mt-2 whitespace-pre-line">{o.selection_process}</p></>}
      <p className="mt-8"><a className="inline-flex rounded-md bg-electric-blue px-5 py-3 font-medium text-arctic-white" href={o.apply_url} target="_blank" rel="noopener noreferrer">Apply on the official page<span className="sr-only"> (opens in a new tab)</span></a></p>
      <div className="mt-4"><TrackButton slug={o.slug} /></div>
      <p className="mt-4 text-sm text-slate">Samarthya does not take part in selection and cannot guarantee any outcome. Never pay to apply for an opportunity listed here.</p>
      <Source p={o.provenance} />
    </div></Section></>);
}

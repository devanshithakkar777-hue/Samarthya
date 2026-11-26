import type { Metadata } from "next";
import { apiBase } from "@/lib/api";
import { notFound } from "next/navigation";
import { PageHead, Section } from "@/components/ui";

type P = { display_name: string; headline: string | null; bio: string | null; links: string[]; indexable: boolean; note: string;
  entries: { section: string; title: string; organisation: string | null; dates: string; detail: string | null; bullets: string[]; evidence: { kind: string; url: string }[] }[] };

async function load(slug: string): Promise<P> {
  const res = await fetch(`${apiBase}/v1/portfolios/${encodeURIComponent(slug)}`, { cache: "no-store" });
  if (res.status === 404) notFound();
  if (!res.ok) throw new Error("unavailable");
  return res.json();
}
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const p = await load((await params).slug);
  return { title: p.display_name, robots: p.indexable ? undefined : { index: false, follow: false } };
}
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const p = await load((await params).slug);
  const bySec = p.entries.reduce<Record<string, P["entries"]>>((a, e) => { (a[e.section] ??= []).push(e); return a; }, {});
  return (<><PageHead title={p.display_name} lead={p.headline ?? undefined} />
    <Section><div className="max-w-3xl">{p.bio && <p className="whitespace-pre-line text-lg">{p.bio}</p>}
      {Object.entries(bySec).map(([s, es]) => <section key={s} className="mt-8"><h2 className="text-xl font-semibold capitalize">{s}</h2>{es.map((e, i) => <div key={i} className="mt-3"><h3 className="font-medium">{e.title}{e.organisation ? `, ${e.organisation}` : ""} <span className="text-sm font-normal text-slate">{e.dates}</span></h3>{e.detail && <p className="text-sm text-slate">{e.detail}</p>}
        {e.bullets.length > 0 && <ul className="list-disc pl-5">{e.bullets.map((b, k) => <li key={k}>{b}</li>)}</ul>}
        {e.evidence.length > 0 && <p className="text-sm">{e.evidence.map((v, k) => <a key={k} className="mr-3 text-electric-blue underline" href={v.url} target="_blank" rel="noopener noreferrer nofollow">{v.kind}<span className="sr-only"> (opens in a new tab)</span></a>)}</p>}</div>)}</section>)}
      {p.links.length > 0 && <p className="mt-8">{p.links.map((l) => <a key={l} className="mr-4 text-electric-blue underline" href={l} target="_blank" rel="noopener noreferrer nofollow">{l}</a>)}</p>}
      <p className="mt-10 text-sm text-slate">{p.note}</p></div></Section></>);
}

import type { Metadata } from "next";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { Card, fmtDate, PageHead, Section, Source } from "@/components/ui";

type B = { slug: string; category: string; region: string | null; event_date: string; headline: string; sections: { title: string; text: string | null }[]; connects_to: string[]; provenance: Provenance; related: { slug: string; headline: string; category: string }[] };
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { return { title: (await apiGet<B>(`/v1/briefs/${(await params).slug}`)).headline }; }
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const b = await apiGet<B>(`/v1/briefs/${(await params).slug}`);
  return (<><PageHead title={b.headline} lead={`${b.category}${b.region ? ` · ${b.region}` : ""} · ${fmtDate(b.event_date)}`} crumbs={[{ href: "/explore", label: "Explore" }, { href: "/world", label: "World" }]} />
    <Section><article className="max-w-3xl">{b.sections.filter((s) => s.text).map((s) => <section key={s.title} className="mb-6"><h2 className="text-xl font-semibold">{s.title}</h2><p className="mt-2 whitespace-pre-line">{s.text}</p></section>)}
      <p className="text-sm text-slate">&ldquo;What could happen next&rdquo; lists possibilities, not predictions. Samarthya takes no side on contested politics; read the cited sources and decide for yourself.</p>
      <Source p={b.provenance} /></article>
      {b.related.length > 0 && <><h2 className="mb-3 mt-10 text-xl font-semibold">Related</h2><ul className="grid gap-4 md:grid-cols-3">{b.related.map((r) => <li key={r.slug}><Card href={`/world/briefs/${r.slug}`} title={r.headline}>{r.category}</Card></li>)}</ul></>}
      <p className="mt-8 text-sm"><Link className="text-electric-blue underline" href="/report">Report a mistake</Link></p></Section></>);
}

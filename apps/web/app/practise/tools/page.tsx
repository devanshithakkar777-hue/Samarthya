import type { Metadata } from "next";
import { apiTry } from "@/lib/api";
import { PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Jugaad Lab tools" };
type T = { slug: string; name: string; category: string; what_for: string; free_option?: string; paid_details?: string; url: string; learn_url?: string; provenance?: { last_verified?: string } };
export default async function Page() {
  const d = await apiTry<{ results: T[]; note: string }>("/v1/practical-tools", { results: [], note: "" }, 120);
  const cats = [...new Set(d.results.map((t) => t.category))];
  return (<><PageHead title="Tools worth knowing" lead="Free and paid tools that save time, with a link to the official page for the latest plan and price." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section>{d.results.length === 0 ? <p className="text-slate">No tools are published yet. They appear after an editor and a reviewer check them against the official page.</p> : <>
      <p className="mb-6 text-slate">{d.note}</p>
      {cats.map((c) => <section key={c} aria-labelledby={`c-${c}`} className="mb-8"><h2 id={`c-${c}`} className="mb-3 text-2xl font-semibold capitalize">{c.replace(/-/g, " ")}</h2>
        <ul className="grid gap-3 md:grid-cols-2">{d.results.filter((t) => t.category === c).map((t) => <li key={t.slug} className="rounded-md border border-ink/10 bg-white p-4"><h3 className="text-lg font-semibold">{t.name}</h3><p>{t.what_for}</p>
          {t.free_option && <p className="mt-1 text-sm"><strong>Free:</strong> {t.free_option}</p>}{t.paid_details && <p className="text-sm"><strong>Paid:</strong> {t.paid_details}</p>}
          <p className="mt-2 text-sm"><a className="text-electric-blue underline" href={t.url} rel="noopener noreferrer">Official site</a>{t.learn_url && <> · <a className="text-electric-blue underline" href={t.learn_url} rel="noopener noreferrer">Learn it</a></>}{t.provenance?.last_verified && <span className="text-slate"> · checked {t.provenance.last_verified}</span>}</p></li>)}</ul></section>)}</>}</Section></>);
}

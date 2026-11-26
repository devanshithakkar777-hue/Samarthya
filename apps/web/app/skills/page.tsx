import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import { Card, Empty, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Skills" };
type S = { slug: string; name: string; category: string; overview: string };

export default async function Page() {
  const { results } = await apiGet<{ results: S[] }>("/v1/skills");
  const by = new Map<string, S[]>();
  for (const s of results) by.set(s.category, [...(by.get(s.category) ?? []), s]);
  return (
    <>
      <PageHead title="Skills" lead="Each skill page lists free and paid ways to learn it, with the provider and price stated." crumbs={[{ href: "/learn", label: "Learn" }]} />
      <Section>
        {results.length === 0 ? <Empty title="No skills published yet" /> : [...by].map(([cat, ss]) => (
          <div key={cat} className="mb-8"><h2 className="mb-3 text-xl font-semibold">{cat}</h2>
            <ul className="grid gap-4 md:grid-cols-3">{ss.map((s) => <li key={s.slug}><Card href={`/skills/${s.slug}`} title={s.name}>{s.overview}</Card></li>)}</ul></div>))}
      </Section>
    </>
  );
}

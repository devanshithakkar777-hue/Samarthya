import Link from "next/link";
import { apiTry } from "@/lib/api";
import type { Pillar } from "@/lib/nav";
import { Card, PageHead, Section } from "./ui";

type Cov = { pillars: Pillar[] };

/** A destination page: the pillars that live here, with an honest count of what is published today. */
export default async function Hub({ dest, title, lead, extra }: { dest: string; title: string; lead: string; extra?: React.ReactNode }) {
  const cov = await apiTry<Cov>("/v1/content-coverage", { pillars: [] }, 120);
  const items = cov.pillars.filter((p) => p.destination === dest);
  return (
    <>
      <PageHead title={title} lead={lead} />
      <Section>
        <ul className="grid gap-4 md:grid-cols-2">
          {items.map((p) => (
            <li key={p.number}>
              <Card href={p.path} title={p.name}>
                {p.published_items === null ? "Tools for your own use." : p.published_items > 0 ? `${p.published_items} published so far.` : "Being prepared. Nothing is published here until it has been sourced and reviewed."}
              </Card>
            </li>
          ))}
        </ul>
        {items.length === 0 && <p className="text-slate">The service is not reachable right now. <Link className="text-electric-blue underline" href="/explore">Browse careers</Link> meanwhile.</p>}
        {extra}
      </Section>
    </>
  );
}

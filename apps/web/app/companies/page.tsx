import type { Metadata } from "next";
import { Card, Empty, PageHead, Section } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { CompanyCard } from "@/lib/types";

export const metadata: Metadata = { title: "Companies" };
export const dynamic = "force-dynamic";

export default async function Companies() {
  const list = await apiGet<CompanyCard[]>("/v1/companies");
  return (
    <>
      <PageHead title="Companies that hire in these fields" lead="Each company links to its own official careers page. We show only pages we have checked." />
      <Section>
        {list.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((c) => (<Card key={c.id} href={`/companies/${c.slug}`} title={c.name}><p>{c.summary}</p></Card>))}
          </div>
        ) : (<Empty title="No companies are published yet">Check back soon.</Empty>)}
      </Section>
    </>
  );
}

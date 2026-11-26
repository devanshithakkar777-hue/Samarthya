import type { Metadata } from "next";
import Link from "next/link";
import { Card, Empty, PageHead, Section } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { SectorCard } from "@/lib/types";

export const metadata: Metadata = { title: "Explore careers" };
export const dynamic = "force-dynamic";

export default async function Explore() {
  const sectors = await apiGet<SectorCard[]>("/v1/sectors");
  return (
    <>
      <PageHead title="Explore careers by sector" lead="Each sector lists the roles in it, the degrees that lead there, and what each role asks for. Every page shows its source and when it was last checked." />
      <Section>
        <nav aria-label="More ways to explore" className="mb-8 flex flex-wrap gap-x-6 gap-y-2 text-lg">
          {[["/explore/discover", "Discover your interests"], ["/explore/career-switch", "Career-switch roadmap"], ["/opportunities", "Opportunities"], ["/applications", "My applications"], ["/companies", "Companies"], ["/pathways", "Education pathways"], ["/world", "World and global awareness"], ["/world/daily", "Daily world briefing"], ["/briefing", "Weekly briefing"], ["/roadmap", "Roadmap"], ["/ask", "Ask a sourced question"], ["/explore/exams", "Which exam fits me?"], ["/explore/study-abroad", "Study abroad cost planner"], ["/explore/pay", "Pay ranges"], ["/world/map", "Connect the dots"]].map(([h, l]) => (
            <Link key={h} className="text-electric-blue underline" href={h}>{l}</Link>))}
        </nav>
        {sectors.length ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sectors.map((s) => (
              <Card key={s.id} href={`/explore/${s.slug}`} title={s.name}>
                <p>{s.summary}</p>
                <p className="mt-2 text-electric-blue">{s.role_count} {s.role_count === 1 ? "role" : "roles"}</p>
              </Card>
            ))}
          </div>
        ) : (
          <Empty title="No sectors are published yet">We only publish a sector after its facts are reviewed against a source. Please check back soon.</Empty>
        )}
      </Section>
    </>
  );
}

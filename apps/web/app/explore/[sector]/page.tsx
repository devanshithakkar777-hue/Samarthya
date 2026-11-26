import type { Metadata } from "next";
import { Card, PageHead, Section, Source } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { SectorDetail } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;
type P = { params: Promise<{ sector: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { sector } = await params;
  try { return { title: (await apiGet<SectorDetail>(`/v1/sectors/${sector}`)).name }; } catch { return { title: "Sector" }; }
}

export default async function SectorPage({ params }: P) {
  const { sector } = await params;
  const s = await apiGet<SectorDetail>(`/v1/sectors/${sector}`);
  return (
    <>
      <PageHead title={s.name} lead={s.summary} crumbs={[{ href: "/explore", label: "Explore" }]} />
      <Section title="Roles in this sector">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {s.roles.map((r) => (<Card key={r.id} href={`/roles/${r.slug}`} title={r.title}><p>{r.job_family} · {r.level}</p></Card>))}
        </div>
        {!s.roles.length && <p className="text-slate">No roles are published in this sector yet.</p>}
      </Section>
      {s.education_routes.length > 0 && (
        <Section title="Degrees that lead here">
          <ul className="grid gap-3 md:grid-cols-2">
            {s.education_routes.map((e) => (
              <li key={e.qualification.slug} className="rounded-lg bg-white p-4 shadow-sm">
                <p className="font-medium">{e.qualification.degree}{e.qualification.specialization ? `, ${e.qualification.specialization}` : ""}</p>
                <p className="text-sm text-slate">{e.strength === 3 ? "Direct route" : e.strength === 2 ? "Common route" : "Possible route"}. {e.reason}</p>
              </li>
            ))}
          </ul>
        </Section>
      )}
      <Section><Source p={s} /></Section>
    </>
  );
}

import type { Metadata } from "next";
import { PageHead, Section, Source } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { SkillDetail } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;
type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  try { return { title: (await apiGet<SkillDetail>(`/v1/skills/${slug}`)).name }; } catch { return { title: "Skill" }; }
}

export default async function SkillPage({ params }: P) {
  const { slug } = await params;
  const s = await apiGet<SkillDetail>(`/v1/skills/${slug}`);
  return (
    <>
      <PageHead title={s.name} lead={s.overview} crumbs={[{ href: "/explore", label: "Explore" }]} />
      <Section title="Ways to learn it">
        {s.resources.length ? (
          <ul className="grid gap-4 md:grid-cols-2">
            {s.resources.map((r) => (
              <li key={r.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
                <h3 className="font-semibold"><a className="text-electric-blue underline" href={r.url} target="_blank" rel="noopener noreferrer">{r.title}<span className="sr-only"> (opens in a new tab)</span></a></h3>
                <p className="mt-1 text-sm text-slate">
                  {r.provider} · {r.format} · {r.level} · {r.language}{r.duration_hours ? ` · about ${r.duration_hours} hours` : ""}
                </p>
                <p className="mt-2 text-sm"><strong>{r.free ? "Free" : `₹${r.price_inr}`}</strong>{r.certificate ? " · certificate available" : ""}{r.sponsored ? " · sponsored listing" : ""}</p>
                <Source p={r} />
              </li>
            ))}
          </ul>
        ) : <p className="text-slate">We have not published learning resources for this skill yet. We list only options we have checked.</p>}
        <Source p={s} />
      </Section>
    </>
  );
}

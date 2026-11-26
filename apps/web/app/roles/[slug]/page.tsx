import type { Metadata } from "next";
import Link from "next/link";
import RoleChecklist from "@/components/RoleChecklist";
import { PageHead, Section, Source, fmtDate } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { RoleDetail } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;
type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  try { return { title: (await apiGet<RoleDetail>(`/v1/roles/${slug}`)).title }; } catch { return { title: "Role" }; }
}

export default async function RolePage({ params }: P) {
  const { slug } = await params;
  const r = await apiGet<RoleDetail>(`/v1/roles/${slug}`);
  return (
    <>
      <PageHead title={r.title} lead={r.description} crumbs={[{ href: "/explore", label: "Explore" }, { href: `/explore/${r.sector.slug}`, label: r.sector.name }]} />
      <Section title="What this role asks for">
        <RoleChecklist requirements={r.requirements} />
        <Source p={r} />
      </Section>
      {r.entry_degrees.length > 0 && (
        <Section title="Degrees that can lead here">
          <ul className="grid gap-3 md:grid-cols-2">
            {r.entry_degrees.map((d) => (
              <li key={d.slug} className="rounded-lg bg-white p-4 shadow-sm">
                {d.degree}{d.specialization ? `, ${d.specialization}` : ""}{d.note && <span className="block text-sm text-slate">{d.note}</span>}
              </li>
            ))}
          </ul>
        </Section>
      )}
      {r.progression && <Section title="How this career grows"><p className="max-w-3xl text-lg">{r.progression}</p></Section>}
      <Section title="Where to look for openings">
        {r.employers.length ? (
          <ul className="grid gap-3 md:grid-cols-2">
            {r.employers.map((e) => (
              <li key={e.slug} className="rounded-lg bg-white p-4 shadow-sm">
                <Link href={`/companies/${e.slug}`} className="font-medium text-electric-blue underline">{e.company}</Link>
                <p className="text-sm text-slate">
                  <a className="underline" href={e.careers_url} target="_blank" rel="noopener noreferrer">Official careers page<span className="sr-only"> (opens in a new tab)</span></a>
                  . Link checked {fmtDate(e.last_verified)}.
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-slate">We have not verified any hiring pages for this role yet. We never invent them. Try the official websites of employers in this sector.</p>
        )}
        <p className="mt-4 text-sm text-slate">Samarthya does not place students or take fees. Applications happen on the employer&apos;s own page.</p>
      </Section>
    </>
  );
}

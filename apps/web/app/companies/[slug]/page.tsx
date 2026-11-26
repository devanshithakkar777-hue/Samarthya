import type { Metadata } from "next";
import Link from "next/link";
import { PageHead, Section, Source, fmtDate } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { CompanyDetail } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;
type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  try { return { title: (await apiGet<CompanyDetail>(`/v1/companies/${slug}`)).name }; } catch { return { title: "Company" }; }
}

export default async function CompanyPage({ params }: P) {
  const { slug } = await params;
  const c = await apiGet<CompanyDetail>(`/v1/companies/${slug}`);
  return (
    <>
      <PageHead title={c.name} lead={c.summary} crumbs={[{ href: "/companies", label: "Companies" }]} />
      <Section><p><Link className="font-medium text-electric-blue underline" href={`/companies/${slug}/prep`}>Preparing for {c.name}: guide and practice</Link></p></Section>
      <Section title="Roles and official hiring pages">
        {c.roles.length ? (
          <ul className="grid gap-3 md:grid-cols-2">
            {c.roles.map((r) => (
              <li key={r.slug} className="rounded-lg bg-white p-4 shadow-sm">
                <Link className="font-medium text-electric-blue underline" href={`/roles/${r.slug}`}>{r.title}</Link>
                <p className="text-sm text-slate"><a className="underline" href={r.careers_url} target="_blank" rel="noopener noreferrer">Official careers page<span className="sr-only"> (opens in a new tab)</span></a>. Checked {fmtDate(r.last_verified)}.</p>
              </li>
            ))}
          </ul>
        ) : <p className="text-slate">No verified hiring pages yet.</p>}
        {c.website && <p className="mt-4 text-sm">Company website: <a className="text-electric-blue underline" href={c.website} target="_blank" rel="noopener noreferrer">{c.website}</a></p>}
        <Source p={c} />
      </Section>
    </>
  );
}

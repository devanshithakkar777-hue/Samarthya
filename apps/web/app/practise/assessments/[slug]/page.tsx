import type { Metadata } from "next";
import Assessment from "@/components/practise/Assessment";
import Private from "@/components/kit/Private";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { PageHead, Section, Source } from "@/components/ui";

type A = { title: string; description: string; duration_minutes: number | null; credential: { statement: string; issuer: string | null; official_url: string | null }; provenance: Provenance };
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { return { title: (await apiGet<A>(`/v1/assessments/${(await params).slug}`)).title }; }
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const slug = (await params).slug;
  const a = await apiGet<A>(`/v1/assessments/${slug}`);
  return (<><PageHead title={a.title} lead={a.description} crumbs={[{ href: "/practise", label: "Practise" }, { href: "/practise/assessments", label: "Assessments" }]} />
    <Section><p className="mb-6 max-w-2xl rounded-md border border-ink/10 bg-white p-3 text-sm text-slate">{a.credential.statement}{a.credential.official_url && <> <a className="text-electric-blue underline" href={a.credential.official_url} target="_blank" rel="noopener noreferrer">Official page<span className="sr-only"> (opens in a new tab)</span></a>.</>}</p>
      <Private><Assessment slug={slug} duration={a.duration_minutes} /></Private><Source p={a.provenance} /></Section></>);
}

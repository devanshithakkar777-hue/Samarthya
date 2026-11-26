import type { Metadata } from "next";
import Link from "next/link";
import { Empty, PageHead, Section } from "@/components/ui";
import { apiGet } from "@/lib/api";

export const dynamic = "force-dynamic";
type P = { params: Promise<{ slug: string }> };
type Pack = { company: { slug: string; name: string }; roles: { slug: string; title: string; careers_url: string }[]; lessons: { slug: string; title: string; summary: string; minutes: number | null }[]; questions: { slug: string; stem: string }[]; empty: boolean; note: string };

export async function generateMetadata({ params }: P): Promise<Metadata> { const { slug } = await params; return { title: `Prepare for ${slug}` }; }
export default async function Page({ params }: P) {
  const { slug } = await params;
  const p = await apiGet<Pack>(`/v1/companies/${slug}/prep`);
  return (<><PageHead title={`Prepare for ${p.company.name}`} lead={p.note} crumbs={[{ href: `/companies/${slug}`, label: p.company.name }]} />
    <Section title="Roles and official careers pages"><ul className="grid gap-2">{p.roles.map((r) => <li key={r.slug}><Link className="text-electric-blue underline" href={`/roles/${r.slug}`}>{r.title}</Link> · <a className="underline" href={r.careers_url} target="_blank" rel="noopener noreferrer">Official careers page</a></li>)}</ul></Section>
    {p.empty ? <Section><Empty title="No prep guide yet">Reviewers have not published a prep guide for this company. Nothing has been invented to fill the gap.</Empty></Section> : <>
      <Section title="Lessons"><ul className="grid gap-3">{p.lessons.map((l) => <li key={l.slug}><Link className="font-medium text-electric-blue underline" href={`/academy/${l.slug}`}>{l.title}</Link><p>{l.summary}</p></li>)}</ul></Section>
      <Section title="Practice questions"><ul className="grid gap-2">{p.questions.map((q) => <li key={q.slug}>{q.stem}</li>)}</ul></Section></>}</>);
}

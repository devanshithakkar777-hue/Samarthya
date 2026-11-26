import type { Metadata } from "next";
import { apiGet } from "@/lib/api";
import { Card, Empty, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Assessments" };
type A = { slug: string; title: string; description: string; duration_minutes: number | null; questions: number; credential: { statement: string } };

export default async function Page() {
  const d = await apiGet<{ results: A[] }>("/v1/assessments");
  return (<><PageHead title="Assessments" lead="Check what you know. Results are private. Samarthya badges are our own practice markers, not accredited qualifications, and every page says who issues what." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section>{d.results.length === 0 ? <Empty title="No assessments published yet" /> : (
      <ul className="grid gap-4 md:grid-cols-3">{d.results.map((a) => <li key={a.slug}><Card href={`/practise/assessments/${a.slug}`} title={a.title}>{a.description}<br /><span className="text-xs">{a.questions} questions{a.duration_minutes ? ` · ${a.duration_minutes} min` : ""}</span><br /><span className="text-xs">{a.credential.statement}</span></Card></li>)}</ul>)}</Section></>);
}

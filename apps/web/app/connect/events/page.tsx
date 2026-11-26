import type { Metadata } from "next";
import { apiTry } from "@/lib/api";
import { Card, Empty, fmtDate, PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Events and competitions" };
const KINDS = ["webinar", "expert_talk", "workshop", "conference", "case_competition", "competition", "hackathon", "showcase", "networking_event"];
type O = { slug: string; title: string; organisation: string; kind: string; location: string | null; mode: string | null; deadline: string | null; rolling: boolean };

export default async function Page() {
  const lists = await Promise.all(KINDS.map((k) => apiTry<{ results: O[] }>(`/v1/opportunities?kind=${k}`, { results: [] }, 120)));
  const all = lists.flatMap((l) => l.results);
  return (<><PageHead title="Events and competitions" lead="Talks, webinars, workshops, case competitions, hackathons and showcases. Each is listed with its organiser and a link to the official page." crumbs={[{ href: "/connect", label: "Connect" }]} />
    <Section>{all.length === 0 ? <Empty title="No events published yet">Events appear here once they have been checked against the organiser&apos;s own page.</Empty> : (
      <ul className="grid gap-4 md:grid-cols-2">{all.map((o) => <li key={o.slug}><Card href={`/opportunities/${o.slug}`} title={o.title}>{o.organisation} · {o.kind.replace(/_/g, " ")}<br /><span className="text-xs">{[o.location, o.mode, o.rolling ? "Rolling" : o.deadline ? `By ${fmtDate(o.deadline)}` : null].filter(Boolean).join(" · ")}</span></Card></li>)}</ul>)}</Section></>);
}

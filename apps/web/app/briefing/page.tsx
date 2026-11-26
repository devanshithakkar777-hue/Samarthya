import type { Metadata } from "next";
import Link from "next/link";
import { Empty, PageHead, Section, Source, fmtDate } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { BriefItem } from "@/lib/types";

export const metadata: Metadata = { title: "Weekly briefing" };
export const dynamic = "force-dynamic";

type Item = BriefItem & { week_of: string; related_roles: { slug: string; title: string }[] };

export default async function Briefing() {
  const items = await apiGet<Item[]>("/v1/briefing");
  const weeks = new Map<string, Item[]>();
  items.forEach((n) => weeks.set(n.week_of, [...(weeks.get(n.week_of) ?? []), n]));
  return (
    <>
      <PageHead title="Weekly briefing" lead="Short, sourced updates that matter to students: exams, notifications and changes in hiring. An editor reads each one before it is published, and each says why it matters." />
      <Section>
        {items.length ? [...weeks.entries()].map(([week, list]) => (
          <section key={week} aria-labelledby={`w-${week}`} className="mb-10">
            <h2 id={`w-${week}`} className="mb-4 text-xl font-semibold">Week of {fmtDate(week)}</h2>
            <ul className="grid gap-5">
              {list.map((n) => (
                <li key={n.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
                  <p className="text-sm text-slate">{fmtDate(n.event_date)}{n.sector ? ` · ${n.sector.name}` : ""}</p>
                  <h3 className="mt-1 text-xl font-semibold">{n.headline}</h3>
                  <p className="mt-2">{n.summary}</p>
                  <p className="mt-2"><strong>Why it matters:</strong> {n.why_it_matters}</p>
                  {n.related_roles.length > 0 && (
                    <p className="mt-2 text-sm">Related roles: {n.related_roles.map((r, i) => (<span key={r.slug}>{i > 0 && ", "}<Link className="text-electric-blue underline" href={`/roles/${r.slug}`}>{r.title}</Link></span>))}</p>
                  )}
                  <p className="mt-2"><a className="text-electric-blue underline" href={n.link} target="_blank" rel="noopener noreferrer">Read the official notice<span className="sr-only"> (opens in a new tab)</span></a></p>
                  <Source p={n} />
                </li>
              ))}
            </ul>
          </section>
        )) : <Empty title="Nothing to report right now">We publish an update only when we can link to an official source.</Empty>}
      </Section>
    </>
  );
}

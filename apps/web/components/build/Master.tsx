"use client";

import Crud from "@/components/kit/Crud";
import { Note } from "@/components/kit/Controls";
import { useMine } from "@/lib/useMine";

export const GROWTH = ["workplace_win", "feedback_received", "responsibility", "promotion", "workplace_learning", "plan_30_60_90", "kpi_okr", "promotion_check", "six_month_review", "leadership_log"];
const SECTIONS = ["education", "skill", "project", "internship", "experience", "certification", "achievement", "competition", "leadership", "volunteering", "publication", "extracurricular", "language", "workplace_win", "feedback_received", "responsibility", "promotion", "workplace_learning", "plan_30_60_90", "kpi_okr", "promotion_check", "six_month_review", "leadership_log"];
type Master = { entries: { id: number; section: string; title: string; basis?: string }[] };

export default function Master({ mode = "profile" }: { mode?: "profile" | "growth" }) {
  const growth = mode === "growth";
  const { reload } = useMine<Master>("/v1/me/master");
  return (
    <div className="grid gap-5">
      <Note>{growth ? "Your growth log: wins, feedback, new responsibilities and promotions, kept as you go so reviews and raises are easy to prepare for. Add only what is true." : "This is your master profile: everything true about you, in one place. Resumes are made by choosing from it. Add only what is true and be ready to explain every line. Skills show as “self-reported” until a project or experience backs them up."}</Note>
      <Crud path="/v1/me/master" listKey="entries" noun="entry" onChange={reload} filter={(r) => growth ? GROWTH.includes(String(r.section)) : !GROWTH.includes(String(r.section))} empty="Start with your degree, then a project or two."
        fields={[
          { name: "section", label: "Section", type: "select", options: growth ? GROWTH : SECTIONS.filter((x) => !GROWTH.includes(x)), required: true },
          { name: "title", label: "Title (degree, project, role, skill, certificate)", required: true },
          { name: "organisation", label: "Organisation or institution" }, { name: "location", label: "Location" },
          { name: "start_date", label: "Start", type: "date" }, { name: "end_date", label: "End", type: "date" }, { name: "current", label: "Still ongoing", type: "bool" },
          { name: "detail", label: "One-line detail (grade, scope, level)" },
          { name: "bullets", label: "What you did and achieved (one per line, up to 8)", type: "lines", rows: 6, help: "Say what you did and, where true, the measurable result. Do not exaggerate; you may be asked about each line." },
          { name: "evidence", label: "Evidence links (one per line: kind https://link)", type: "evidence", rows: 3, help: "Kinds: github, portfolio, certificate, publication, presentation, other" },
          { name: "tags", label: "Skills and tools used (one per line)", type: "lines", rows: 3 },
        ]}
        render={(r) => (<><h3 className="font-semibold">{String(r.title)}<span className="ml-2 rounded bg-white px-2 py-0.5 text-xs font-normal text-slate ring-1 ring-ink/20">{String(r.section)}</span>
          {r.basis ? <span className={`ml-2 rounded px-2 py-0.5 text-xs font-normal ${r.basis === "demonstrated" ? "bg-electric-blue text-arctic-white" : "bg-white text-slate ring-1 ring-ink/20"}`}>{String(r.basis)}</span> : null}</h3>
          {r.organisation ? <p className="text-sm text-slate">{String(r.organisation)}</p> : null}
          {Array.isArray(r.bullets) && r.bullets.length > 0 && <ul className="mt-2 list-disc pl-5 text-sm">{(r.bullets as string[]).map((b, i) => <li key={i}>{b}</li>)}</ul>}</>)} />
    </div>
  );
}

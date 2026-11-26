"use client";

import Link from "next/link";
import Crud from "@/components/kit/Crud";
import { Note } from "@/components/kit/Controls";
import { fmtDate } from "@/components/ui";
import { useMine } from "@/lib/useMine";

type Rem = { id: number; title: string; kind: string; date: string; days_left: number };
const MSG: Record<string, string> = { deadline: "deadline", missed: "deadline passed", follow_up: "follow up" };

export default function Applications() {
  const { data, reload } = useMine<Rem[]>("/v1/me/applications/reminders");
  return (
    <div className="grid gap-5">
      {data && data.length > 0 && <Note>{data.map((r) => `${r.title}: ${MSG[r.kind]} ${r.days_left === 0 ? "today" : r.days_left > 0 ? `in ${r.days_left} day(s)` : `${-r.days_left} day(s) ago`}`).join(". ")}.</Note>}
      <p><a className="text-electric-blue underline" href="/api/proxy/v1/me/applications.ics">Add deadlines to my calendar (.ics)</a>. Find more on <Link className="text-electric-blue underline" href="/opportunities">Opportunities</Link>.</p>
      <Crud path="/v1/me/applications" listKey="items" noun="application" onChange={reload} empty="Nothing tracked yet. Add one, or press Track on any opportunity."
        fields={[{ name: "title", label: "Role or opportunity", required: true }, { name: "organisation", label: "Organisation" }, { name: "apply_url", label: "Link (https://)" },
          { name: "status", label: "Status", type: "select", options: ["saved", "preparing", "applied", "interview", "offer", "rejected", "withdrawn"] },
          { name: "deadline", label: "Deadline", type: "date" }, { name: "follow_up", label: "Follow up on", type: "date" }, { name: "notes", label: "Notes", type: "textarea", rows: 3 }]}
        render={(r) => (<><h3 className="font-semibold">{String(r.title)}{r.organisation ? <span className="font-normal text-slate"> · {String(r.organisation)}</span> : null}</h3>
          <p className="text-sm"><strong>{String(r.status)}</strong>{r.deadline ? ` · deadline ${fmtDate(String(r.deadline))}` : ""}{r.follow_up ? ` · follow up ${fmtDate(String(r.follow_up))}` : ""}</p>
          {r.apply_url ? <p className="text-sm"><a className="text-electric-blue underline" href={String(r.apply_url)} target="_blank" rel="noopener noreferrer">Open the page<span className="sr-only"> (opens in a new tab)</span></a></p> : null}</>)} />
    </div>
  );
}

"use client";

import Link from "next/link";
import Crud from "@/components/kit/Crud";
import { Note } from "@/components/kit/Controls";
import { useMine } from "@/lib/useMine";
import { fmtDate } from "@/components/ui";

type S = { overdue: number; this_week: number; weak_topics: { pillar: string; topic: string; accuracy: number; attempts: number }[] };

export default function Planner() {
  const { data, reload } = useMine<S>("/v1/me/study");
  return (
    <div className="grid gap-5">
      {data && (
        <Note>{data.overdue > 0 ? `${data.overdue} overdue. ` : ""}{data.this_week} due in the next 7 days.
          {data.weak_topics.length > 0 && <> Topics worth another go: {data.weak_topics.slice(0, 3).map((w, i) => (<span key={w.topic}>{i ? ", " : ""}<Link className="text-electric-blue underline" href={`/practise/drill?pillar=${w.pillar}&topic=${encodeURIComponent(w.topic)}`}>{w.topic} ({w.accuracy}%)</Link></span>))}.</>}</Note>
      )}
      <Crud path="/v1/me/study" listKey="items" noun="task" onChange={reload} empty="Nothing planned yet. Add an assignment, exam or goal."
        fields={[
          { name: "kind", label: "Kind", type: "select", required: true, options: ["revision", "assignment", "exam", "practical", "backlog", "reading", "goal"] },
          { name: "title", label: "What", required: true }, { name: "subject", label: "Subject" }, { name: "due_date", label: "Due", type: "date" },
          { name: "status", label: "Status", type: "select", options: ["todo", "doing", "done"] }, { name: "notes", label: "Notes", type: "textarea", rows: 3 },
        ]}
        render={(r) => (<><h3 className="font-semibold">{String(r.title)} <span className="text-sm font-normal text-slate">({String(r.kind)}, {String(r.status)})</span></h3>
          <p className="text-sm text-slate">{[r.subject, r.due_date ? `due ${fmtDate(String(r.due_date))}` : null].filter(Boolean).join(" · ")}</p></>)} />
    </div>
  );
}

"use client";

import { useMine } from "@/lib/useMine";
import { ErrorText, Note } from "@/components/kit/Controls";

type O = { institution: string; sharing_students: number; minimum_group: number; privacy: string; suppressed: boolean; message?: string; unit?: string; batches?: Record<string, number> } & Record<string, unknown>;
const LABEL: Record<string, string> = { has_profile: "Built a profile", has_resume: "Created a resume", practised_interview_questions: "Practised interview questions", practised_questions: "Practised questions", tracking_applications: "Tracking applications" };

export default function InstitutionStaff({ slug }: { slug: string }) {
  const d = useMine<O>(`/v1/institution/${slug}/overview`);
  if (d.error) return <ErrorText>{d.error}</ErrorText>;
  if (!d.data) return <p role="status">Loading…</p>;
  const o = d.data;
  return (
    <div className="grid max-w-3xl gap-5"><Note>{o.privacy}</Note>
      <p className="text-lg">{o.sharing_students} student{o.sharing_students === 1 ? "" : "s"} sharing.</p>
      {o.suppressed ? <p>{o.message}</p> : (<><p className="text-sm text-slate">{o.unit}</p>
        <dl className="grid gap-3 sm:grid-cols-2">{Object.keys(LABEL).map((k) => <div key={k} className="rounded-md border border-ink/10 bg-white p-4"><dt className="text-sm text-slate">{LABEL[k]}</dt><dd className="text-2xl font-semibold">{String(o[k])}%</dd></div>)}</dl>
        {o.batches && Object.keys(o.batches).length > 0 && <p className="text-sm text-slate">Batches large enough to show: {Object.entries(o.batches).map(([y, c]) => `${y} (${c})`).join(", ")}.</p>}</>)}
    </div>
  );
}

"use client";

import Link from "next/link";
import { call } from "@/lib/client";
import { useMine } from "@/lib/useMine";
import { btn, fmtDate } from "@/components/ui";
import { danger, ErrorText } from "@/components/kit/Controls";

type R = { id: number; name: string; target_kind: string; target_ref: string | null; updated_at: string };

export default function ResumeList() {
  const { data, reload, error } = useMine<R[]>("/v1/me/resumes");
  return (
    <div>
      <ErrorText>{error}</ErrorText>
      <Link href="/build/resumes/new" className={btn}>New resume</Link>
      {(data ?? []).length === 0 ? <p className="mt-4 text-slate">No resumes yet. Add entries to your <Link className="text-electric-blue underline" href="/build">master profile</Link> first, then build a resume from them.</p> : (
        <ul className="mt-5 grid gap-3 md:grid-cols-2">{(data ?? []).map((r) => (
          <li key={r.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4"><h3 className="font-semibold"><Link className="text-electric-blue underline" href={`/build/resumes/${r.id}`}>{r.name}</Link></h3>
            <p className="text-sm text-slate">{r.target_kind}{r.target_ref ? `: ${r.target_ref}` : ""} · edited {fmtDate(r.updated_at)}</p>
            <button className={`${danger} mt-3`} onClick={async () => { if (window.confirm("Delete this resume and its saved versions?")) { await call("DELETE", `/v1/me/resumes/${r.id}`); await reload(); } }}>Delete</button></li>))}</ul>)}
    </div>
  );
}

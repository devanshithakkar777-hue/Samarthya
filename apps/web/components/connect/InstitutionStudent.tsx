"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note, small } from "@/components/kit/Controls";

type M = { institution: string; slug: string; share_readiness: boolean; batch_year: number | null; what_is_shared: string } | null;

export default function InstitutionStudent() {
  const d = useMine<M>("/v1/me/institution");
  const [code, setCode] = useState(""); const [share, setShare] = useState(false); const [year, setYear] = useState("");
  const { busy, error, run } = useAction();
  const m = d.data;
  if (d.loading && d.data === null && !d.error) return <p role="status">Loading…</p>;
  return (
    <div className="grid max-w-2xl gap-5">
      <Note>Your institution is never given your name, answers, resume, journal or scores. If you choose to share, it sees only totals for groups of at least 10 students who have also chosen to share. You can turn sharing off or leave at any time.</Note>
      {m ? (<div className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold">{m.institution}</h2><p className="mt-1 text-sm text-slate">{m.what_is_shared}</p>
        <label className="mt-3 flex items-center gap-2"><input type="checkbox" className="h-5 w-5 accent-electric-blue" checked={m.share_readiness} onChange={async (e) => { await run(() => call("PUT", "/v1/me/institution", { share_readiness: e.target.checked, batch_year: m.batch_year })); await d.reload(); }} />Count me in my institution&apos;s totals</label>
        <ErrorText>{error}</ErrorText><button className={`${small} mt-4`} onClick={async () => { if (window.confirm("Leave this institution?")) { await call("DELETE", "/v1/me/institution"); await d.reload(); } }}>Leave institution</button></div>
      ) : (
        <form className="grid gap-4" onSubmit={async (e) => { e.preventDefault(); if (await run(() => call("POST", "/v1/me/institution/join", { code, share_readiness: share, batch_year: year ? Number(year) : null }))) await d.reload(); }}>
          <Labeled id="ic" label="Join code from your institution"><input id="ic" className={inp} required value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" /></Labeled>
          <Labeled id="iy" label="Batch (graduation year, optional)"><input id="iy" inputMode="numeric" className={inp} value={year} onChange={(e) => setYear(e.target.value)} /></Labeled>
          <label className="flex items-center gap-2"><input type="checkbox" className="h-5 w-5 accent-electric-blue" checked={share} onChange={(e) => setShare(e.target.checked)} />Count me in totals shown to my institution (off by default)</label>
          <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Join</button></div></form>)}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";

type Range = { role: string; kind: string; reports: number; range_low: number; range_high: number; basis: string };
const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;

export function PayRanges() {
  const [q, setQ] = useState("");
  const r = useMine<{ results: Range[]; note: string }>(`/v1/salary-ranges${q ? `?role=${encodeURIComponent(q)}` : ""}`);
  return (
    <div className="max-w-3xl grid gap-4"><Note>{r.data?.note ?? "Self-reported pay ranges. Groups under ten are never shown."}</Note>
      <Labeled id="role" label="Search a role"><input id="role" className={inp} value={q} onChange={(e) => setQ(e.target.value)} placeholder="for example analyst" /></Labeled>
      {r.data && r.data.results.length === 0 && <p>No role has enough reports yet to show a range. Ranges appear only when ten or more people have reported for the same role.</p>}
      <ul className="grid gap-2">{r.data?.results.map((x, i) => <li key={i} className="rounded-md border border-ink/10 bg-white p-3"><p className="font-medium">{x.role} <span className="text-sm text-slate">({x.kind === "full_time" ? "full-time, per year" : "internship stipend, per year"})</span></p>
        <p>{inr(x.range_low)} to {inr(x.range_high)} <span className="text-sm text-slate">· {x.reports} reports · {x.basis}</span></p></li>)}</ul>
    </div>
  );
}

export function AddPay() {
  const mine = useMine<{ results: { id: number; role_title: string; city: string; kind: string; annual_amount: number }[] }>("/v1/me/salary-reports");
  const [f, setF] = useState({ role_title: "", city: "", kind: "full_time", years_experience: "0", annual_amount: "" });
  const [ok, setOk] = useState("");
  const { busy, error, run } = useAction();
  async function add(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<{ note: string }>("POST", "/v1/me/salary-reports", { ...f, years_experience: Number(f.years_experience), annual_amount: Number(f.annual_amount) }));
    if (r) { setOk(r.note); setF({ ...f, role_title: "", annual_amount: "" }); void mine.reload(); }
  }
  return (
    <div className="max-w-xl grid gap-4"><Note>Optional and anonymous to others. Your figure is never shown alone. Report only a real figure from your own offer or job.</Note>
      <form onSubmit={add} className="grid gap-3">
        <Labeled id="rt" label="Role title"><input id="rt" required minLength={2} className={inp} value={f.role_title} onChange={(e) => setF({ ...f, role_title: e.target.value })} /></Labeled>
        <Labeled id="ct" label="City"><input id="ct" required minLength={2} className={inp} value={f.city} onChange={(e) => setF({ ...f, city: e.target.value })} /></Labeled>
        <Labeled id="kd" label="Kind"><select id="kd" className={inp} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}><option value="full_time">Full-time (yearly fixed pay)</option><option value="internship_stipend">Internship stipend (per year equivalent)</option></select></Labeled>
        <Labeled id="ye" label="Years of experience"><input id="ye" type="number" min={0} max={45} className={inp} value={f.years_experience} onChange={(e) => setF({ ...f, years_experience: e.target.value })} /></Labeled>
        <Labeled id="am" label="Yearly amount (₹)"><input id="am" type="number" min={0} required className={inp} value={f.annual_amount} onChange={(e) => setF({ ...f, annual_amount: e.target.value })} /></Labeled>
        <ErrorText>{error}</ErrorText>{ok && <p role="status">{ok}</p>}<div><button className={btn} disabled={busy}>Add my figure</button></div></form>
      {mine.data && mine.data.results.length > 0 && <ul className="grid gap-2">{mine.data.results.map((x) => <li key={x.id} className="flex items-center justify-between rounded-md border border-ink/10 bg-white p-3"><span>{x.role_title}, {x.city}: {inr(x.annual_amount)}</span>
        <button className={danger} onClick={async () => { await call("DELETE", `/v1/me/salary-reports/${x.id}`); void mine.reload(); }}>Delete</button></li>)}</ul>}
    </div>
  );
}

type Req = { id: number; context: string; share_path: string; count: number; notes: { strengths: string; improve: string }[]; note: string | null };
export function MyFeedback() {
  const d = useMine<{ results: Req[] }>("/v1/me/feedback-requests");
  const [ctx, setCtx] = useState("");
  const { busy, error, run } = useAction();
  async function add(e: React.FormEvent) { e.preventDefault(); if (await run(() => call("POST", "/v1/me/feedback-requests", { context: ctx }))) { setCtx(""); void d.reload(); } }
  return (
    <div className="max-w-3xl grid gap-4"><Note>Ask people you worked with for private feedback on one piece of work. They reply signed in, you never see their names, and replies show only after three people have answered.</Note>
      <form onSubmit={add} className="grid gap-3"><Labeled id="cx" label="What is it about?" help="For example: our hackathon project, my presentation skills this semester"><input id="cx" required minLength={3} maxLength={200} className={inp} value={ctx} onChange={(e) => setCtx(e.target.value)} /></Labeled><ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Create a request</button></div></form>
      <ul className="grid gap-3">{d.data?.results.map((r) => <li key={r.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{r.context}</p>
        <p className="text-sm text-slate">Share this path with the people you worked with: <code>{r.share_path}</code> · {r.count} replies</p>{r.note && <p className="text-sm">{r.note}</p>}
        {r.notes.length > 0 && <ul className="mt-2 grid gap-2">{r.notes.map((n, i) => <li key={i} className="rounded bg-arctic-white p-2 text-sm"><p><strong>Went well:</strong> {n.strengths}</p><p><strong>Could grow:</strong> {n.improve}</p></li>)}</ul>}
        <button className={`${danger} mt-2`} onClick={async () => { await call("DELETE", `/v1/me/feedback-requests/${r.id}`); void d.reload(); }}>Delete request</button></li>)}</ul>
    </div>
  );
}

export function GiveFeedback({ token }: { token: string }) {
  const c = useMine<{ context: string; own: boolean; guide: string }>(`/v1/me/feedback-give/${token}`);
  const [f, setF] = useState({ strengths: "", improve: "" });
  const [done, setDone] = useState(false);
  const { busy, error, run } = useAction();
  if (c.error) return <ErrorText>{c.error}</ErrorText>;
  if (!c.data) return <p role="status">Loading…</p>;
  if (done) return <p role="status">Thank you. Your reply was saved without your name.</p>;
  return (
    <form onSubmit={async (e) => { e.preventDefault(); if (await run(() => call("POST", `/v1/me/feedback-give/${token}`, f))) setDone(true); }} className="grid max-w-xl gap-3">
      <Note>{c.data.guide}</Note><p>About: <strong>{c.data.context}</strong></p>
      <Labeled id="s" label="What went well?"><textarea id="s" rows={3} required minLength={3} maxLength={600} className={inp} value={f.strengths} onChange={(e) => setF({ ...f, strengths: e.target.value })} /></Labeled>
      <Labeled id="i" label="What could grow?"><textarea id="i" rows={3} required minLength={3} maxLength={600} className={inp} value={f.improve} onChange={(e) => setF({ ...f, improve: e.target.value })} /></Labeled>
      <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy || c.data.own}>Send privately</button></div>{c.data.own && <p className="text-sm">This is your own request, so you cannot reply to it.</p>}
      <p className="text-sm"><Link className="text-electric-blue underline" href="/connect">Back to Connect</Link></p></form>
  );
}

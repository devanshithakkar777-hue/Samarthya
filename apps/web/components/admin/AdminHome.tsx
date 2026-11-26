"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ENTITIES, ENTITY_ORDER } from "@/lib/admin";
import { call } from "@/lib/client";
import Gate from "./Gate";

type Q = { type: string; id: number; label: string; created_by_id: number };
type Stale = { type?: string; entity?: string; id: number; label?: string; last_verified: string | null };
type Unans = { id: number; question: string; times_asked: number };
type Part = { id: number; pathway: string; name: string | null; organisation: string | null; contact: string; message: string | null };
type Rep = { id: number; message: string; page_url: string | null; created_at?: string };

function Body({ role }: { role: string }) {
  const [queue, setQueue] = useState<Q[]>([]);
  const [stale, setStale] = useState<Stale[]>([]);
  const [reps, setReps] = useState<Rep[]>([]);
  const [un, setUn] = useState<Unans[]>([]);
  const [part, setPart] = useState<Part[]>([]);
  const [err, setErr] = useState("");
  const isAdmin = role === "admin";
  const reviewer = role === "reviewer" || role === "admin";

  const load = () => {
    setErr("");
    if (reviewer) call<Q[]>("GET", "/v1/admin/queue").then(setQueue).catch((e: Error) => setErr(e.message));
    call<Stale[]>("GET", "/v1/admin/stale").then(setStale).catch((e: Error) => setErr(e.message));
    call<Unans[]>("GET", "/v1/admin/unanswered").then(setUn).catch(() => {});
    if (isAdmin) call<Part[]>("GET", "/v1/admin/participation").then(setPart).catch(() => {});
    call<Rep[]>("GET", "/v1/admin/reports").then(setReps).catch((e: Error) => setErr(e.message));
  };
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  const resolve = async (id: number, status: "resolved" | "dismissed") => {
    const note = status === "resolved" ? window.prompt("What did you change? (optional)") ?? "" : "";
    try { await call("POST", `/v1/admin/reports/${id}/resolve`, { status, note }); load(); } catch (e) { setErr((e as Error).message); }
  };

  const done = async (path: string) => { try { await call("POST", path); load(); } catch (e) { setErr((e as Error).message); } };
  return (
    <div className="grid gap-10">
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      <section aria-labelledby="create"><h2 id="create" className="mb-3 text-xl font-semibold">Content</h2>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {ENTITY_ORDER.map((k) => (<li key={k}><Link className="block rounded-lg border border-ink/10 bg-white p-4 font-medium hover:border-electric-blue" href={`/admin/${k}`}>{ENTITIES[k].plural}</Link></li>))}
          <li><Link className="block rounded-lg border border-ink/10 bg-white p-4 font-medium hover:border-electric-blue" href="/admin/sources">Sources</Link></li>
          {reviewer && <li><Link className="block rounded-lg border border-ink/10 bg-white p-4 font-medium hover:border-electric-blue" href="/admin/moderation">Moderation and mentors</Link></li>}
          {isAdmin && <li><Link className="block rounded-lg border border-ink/10 bg-white p-4 font-medium hover:border-electric-blue" href="/admin/institutions">Institutions</Link></li>}
        </ul></section>
      {reviewer && (
        <section aria-labelledby="queue"><h2 id="queue" className="mb-3 text-xl font-semibold">Waiting for your review ({queue.length})</h2>
          {queue.length ? <ul className="grid gap-2">{queue.map((q) => (
            <li key={`${q.type}-${q.id}`} className="rounded-lg bg-white p-3 shadow-sm"><Link className="text-electric-blue underline" href={`/admin/${q.type}/${q.id}`}>{q.label}</Link> <span className="text-slate">({ENTITIES[q.type]?.singular ?? q.type})</span></li>))}</ul>
            : <p className="text-slate">Nothing waiting.</p>}</section>
      )}
      <section aria-labelledby="rep"><h2 id="rep" className="mb-3 text-xl font-semibold">Student reports ({reps.length})</h2>
        {reps.length ? <ul className="grid gap-3">{reps.map((r) => (
          <li key={r.id} className="rounded-lg bg-white p-4 shadow-sm"><p>{r.message}</p>
            {r.page_url && <p className="text-sm text-slate">Page: {r.page_url}</p>}
            <div className="mt-2 flex gap-3 text-sm"><button className="text-electric-blue underline" onClick={() => resolve(r.id, "resolved")}>Mark fixed</button><button className="underline" onClick={() => resolve(r.id, "dismissed")}>Dismiss</button></div></li>))}</ul>
          : <p className="text-slate">No open reports.</p>}</section>
      <section aria-labelledby="un"><h2 id="un" className="mb-3 text-xl font-semibold">Questions students asked that we could not answer ({un.length})</h2>
        {un.length ? <ul className="grid gap-2">{un.map((u) => (<li key={u.id} className="flex items-center justify-between gap-3 rounded-lg bg-white p-3 shadow-sm"><span>{u.question} <span className="text-slate">(asked {u.times_asked}×)</span></span><button className="text-sm underline" onClick={() => done(`/v1/admin/unanswered/${u.id}/handled`)}>Now covered</button></li>))}</ul> : <p className="text-slate">No unanswered questions.</p>}</section>
      {isAdmin && (
        <section aria-labelledby="pt"><h2 id="pt" className="mb-3 text-xl font-semibold">Offers to help ({part.length})</h2>
          {part.length ? <ul className="grid gap-2">{part.map((p) => (<li key={p.id} className="rounded-lg bg-white p-3 shadow-sm"><strong>{p.pathway}</strong> · {p.name ?? "no name"}{p.organisation ? `, ${p.organisation}` : ""} · <a className="text-electric-blue underline" href={`mailto:${p.contact}`}>{p.contact}</a>{p.message && <p className="text-sm text-slate">{p.message}</p>}<button className="mt-1 text-sm underline" onClick={() => done(`/v1/admin/participation/${p.id}/handled`)}>Replied</button></li>))}</ul> : <p className="text-slate">None waiting.</p>}</section>
      )}
      <section aria-labelledby="stale"><h2 id="stale" className="mb-3 text-xl font-semibold">Needs re-checking ({stale.length})</h2>
        {stale.length ? <ul className="grid gap-2">{stale.map((s, i) => { const t = s.type ?? s.entity ?? ""; return (
          <li key={i} className="rounded-lg bg-white p-3 shadow-sm"><Link className="text-electric-blue underline" href={`/admin/${t}/${s.id}`}>{s.label ?? `${t} #${s.id}`}</Link> <span className="text-slate">last checked {s.last_verified ?? "never"}</span></li>); })}</ul>
          : <p className="text-slate">Everything published is within its re-check window.</p>}</section>
    </div>
  );
}
export default function AdminHome() { return <Gate>{(role) => <Body role={role} />}</Gate>; }

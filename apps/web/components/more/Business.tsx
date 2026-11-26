"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, inp, Labeled, Note, small } from "@/components/kit/Controls";

type Sess = { id: number; title: string; description: string; starts_at: string; minutes: number; capacity: number; seats_taken: number; mentor: string | null; mentor_headline: string | null; joined: boolean; meeting_details?: string };
const when = (iso: string) => new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

export function GroupSessions() {
  const s = useMine<{ sessions: Sess[]; note: string }>("/v1/mentor-sessions");
  const { busy, error, run } = useAction();
  const act = async (m: string, id: number) => { await run(() => call(m, `/v1/mentor-sessions/${id}/join`)); void s.reload(); };
  return (
    <div className="max-w-3xl"><Note>{s.data?.note ?? "Group sessions run by approved mentors."}</Note><ErrorText>{error}</ErrorText>
      {s.data && !s.data.sessions.length && <p className="mt-4">No group sessions are scheduled yet. Approved mentors add them here.</p>}
      <ul className="mt-4 grid gap-4">{s.data?.sessions.map((x) => (<li key={x.id} className="rounded-md border border-ink/10 bg-white p-4">
        <h3 className="text-lg font-semibold">{x.title}</h3><p className="text-sm text-slate">{x.mentor}{x.mentor_headline ? `, ${x.mentor_headline}` : ""} · {when(x.starts_at)} · {x.minutes} min · {x.seats_taken}/{x.capacity} seats</p>
        <p className="mt-2 whitespace-pre-wrap">{x.description}</p>
        {x.joined ? <><p className="mt-2 rounded bg-arctic-white p-2"><strong>How to join:</strong> {x.meeting_details || "The mentor will share details."}</p><button className={`${danger} mt-2`} disabled={busy} onClick={() => act("DELETE", x.id)}>Leave session</button></>
          : <button className={`${btn} mt-3`} disabled={busy || x.seats_taken >= x.capacity} onClick={() => act("POST", x.id)}>{x.seats_taken >= x.capacity ? "Full" : "Join"}</button>}</li>))}</ul></div>
  );
}

type Prof = { status: string; requests: Record<string, number>; sessions: { id: number; title: string; starts_at: string; capacity: number; seats_taken: number; upcoming: boolean }[]; note: string };
export function ProfessionalDashboard() {
  const d = useMine<Prof>("/v1/professional/dashboard");
  const [f, setF] = useState({ title: "", description: "", starts_at: "", minutes: 45, capacity: 10, meeting_details: "" });
  const { busy, error, run } = useAction();
  async function add(e: React.FormEvent) { e.preventDefault(); if (await run(() => call("POST", "/v1/mentors/me/sessions", { ...f, starts_at: new Date(f.starts_at).toISOString() }))) { setF({ ...f, title: "", description: "" }); void d.reload(); } }
  if (d.error) return <Note>This dashboard is for mentors. Apply on the Mentors page; a reviewer approves mentors before they appear.</Note>;
  if (!d.data) return <p role="status">Loading…</p>;
  return (<div className="max-w-3xl"><p>Mentor status: <strong>{d.data.status}</strong></p>
    <h2 className="mt-4 text-xl font-semibold">Requests</h2><p>{Object.entries(d.data.requests).map(([k, v]) => `${k}: ${v}`).join(" · ")}</p>
    <h2 className="mt-4 text-xl font-semibold">Your group sessions</h2>
    <ul>{d.data.sessions.map((s) => <li key={s.id}>{s.title}, {when(s.starts_at)}, {s.seats_taken}/{s.capacity} seats {s.upcoming ? "" : "(past)"}</li>)}</ul>
    {d.data.status === "approved" && <form onSubmit={add} className="mt-4 grid gap-3"><h2 className="text-xl font-semibold">Offer a group session</h2>
      <Labeled id="t" label="Title"><input id="t" className={inp} required minLength={3} maxLength={160} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Labeled>
      <Labeled id="d" label="What students will get"><textarea id="d" className={inp} required minLength={10} rows={3} value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></Labeled>
      <Labeled id="w" label="Start time"><input id="w" type="datetime-local" className={inp} required value={f.starts_at} onChange={(e) => setF({ ...f, starts_at: e.target.value })} /></Labeled>
      <Labeled id="c" label="Seats"><input id="c" type="number" min={2} max={50} className={inp} value={f.capacity} onChange={(e) => setF({ ...f, capacity: Number(e.target.value) })} /></Labeled>
      <Labeled id="m" label="How to join (shown only to students who join)" help="Paste your own meeting link. Samarthya does not host calls."><input id="m" className={inp} maxLength={500} value={f.meeting_details} onChange={(e) => setF({ ...f, meeting_details: e.target.value })} /></Labeled>
      <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Publish session</button></div></form>}
    <p className="mt-4 text-sm text-slate">{d.data.note}</p></div>);
}

type Emp = { employer: string; opportunities: { slug: string; title: string; status: string; saves: number | null }[]; note: string };
export function EmployerDashboard() {
  const d = useMine<Emp>("/v1/employer/dashboard");
  const [f, setF] = useState({ title: "", kind: "internship", description: "", eligibility: "", apply_url: "https://", location: "", stipend: "" });
  const { busy, error, run } = useAction(); const [msg, setMsg] = useState("");
  async function add(e: React.FormEvent) { e.preventDefault(); const r = await run(() => call<{ note: string }>("POST", "/v1/employer/opportunities", { ...f, location: f.location || null, stipend: f.stipend || null })); if (r) { setMsg(r.note); void d.reload(); } }
  if (d.error) return <Note>This dashboard is for employer accounts that Samarthya has approved. To list an opportunity, ask to be set up through your institution or the contact on the About page.</Note>;
  if (!d.data) return <p role="status">Loading…</p>;
  return (<div className="max-w-3xl"><h2 className="text-xl font-semibold">{d.data.employer}</h2>
    <ul className="mt-3 grid gap-1">{d.data.opportunities.map((o) => <li key={o.slug}>{o.title} · <strong>{o.status}</strong> · saves: {o.saves ?? "hidden (fewer than 10)"}</li>)}</ul>
    <form onSubmit={add} className="mt-6 grid gap-3"><h3 className="text-lg font-semibold">Submit an opportunity for review</h3>
      <Labeled id="et" label="Title"><input id="et" className={inp} required value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Labeled>
      <Labeled id="ek" label="Type"><select id="ek" className={inp} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>{["internship", "full_time", "part_time", "apprenticeship", "graduate_programme", "management_trainee", "workshop", "webinar", "hackathon"].map((k) => <option key={k}>{k}</option>)}</select></Labeled>
      <Labeled id="ed" label="Description"><textarea id="ed" className={inp} rows={4} required minLength={20} value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></Labeled>
      <Labeled id="ee" label="Who can apply"><textarea id="ee" className={inp} rows={2} required value={f.eligibility} onChange={(e) => setF({ ...f, eligibility: e.target.value })} /></Labeled>
      <Labeled id="eu" label="Apply link (https)"><input id="eu" className={inp} required value={f.apply_url} onChange={(e) => setF({ ...f, apply_url: e.target.value })} /></Labeled>
      <Labeled id="es" label="Stipend (state it honestly, or leave blank)"><input id="es" className={inp} value={f.stipend} onChange={(e) => setF({ ...f, stipend: e.target.value })} /></Labeled>
      <ErrorText>{error}</ErrorText>{msg && <Note>{msg}</Note>}<div><button className={btn} disabled={busy}>Submit as draft</button></div></form>
    <p className="mt-4 text-sm text-slate">{d.data.note}</p></div>);
}

type V = { id: number; name: string; stage: string; problem: string | null; customer: string | null; milestones: { text: string; done: boolean }[]; progress: { done: number; total: number } };
export function Ventures() {
  const d = useMine<{ ventures: V[]; stages: Record<string, string>; note: string }>("/v1/me/ventures");
  const [name, setName] = useState(""); const { busy, error, run } = useAction(); const [ms, setMs] = useState<Record<number, string>>({});
  const save = async (v: V, patch: Partial<V>) => { await run(() => call("PUT", `/v1/me/ventures/${v.id}`, { name: v.name, stage: v.stage, problem: v.problem, customer: v.customer, milestones: v.milestones, ...patch })); void d.reload(); };
  return (<div className="max-w-3xl"><Note>{d.data?.note}</Note>
    <form className="mt-4 flex gap-2" onSubmit={async (e) => { e.preventDefault(); await run(() => call("POST", "/v1/me/ventures", { name })); setName(""); void d.reload(); }}>
      <input aria-label="New venture name" className={inp} placeholder="Name your idea or venture" value={name} maxLength={160} onChange={(e) => setName(e.target.value)} required /><button className={btn} disabled={busy}>Add</button></form>
    <ErrorText>{error}</ErrorText>
    {d.data?.ventures.map((v) => (<section key={v.id} className="mt-6 rounded-md border border-ink/10 bg-white p-4"><h3 className="text-lg font-semibold">{v.name}</h3>
      <label className="mt-2 block text-sm font-medium" htmlFor={`st${v.id}`}>Stage</label>
      <select id={`st${v.id}`} className={inp} value={v.stage} onChange={(e) => save(v, { stage: e.target.value })}>{Object.keys(d.data!.stages).map((k) => <option key={k} value={k}>{k}</option>)}</select>
      <p className="text-sm text-slate">{d.data!.stages[v.stage]}</p>
      <label className="mt-2 block text-sm font-medium" htmlFor={`pr${v.id}`}>The problem and who has it</label>
      <textarea id={`pr${v.id}`} className={inp} rows={2} defaultValue={v.problem ?? ""} onBlur={(e) => e.target.value !== (v.problem ?? "") && save(v, { problem: e.target.value })} />
      <h4 className="mt-3 font-medium">Milestones ({v.progress.done}/{v.progress.total})</h4>
      <ul>{v.milestones.map((m, i) => <li key={i}><label><input type="checkbox" checked={m.done} onChange={() => save(v, { milestones: v.milestones.map((x, j) => (j === i ? { ...x, done: !x.done } : x)) })} /> {m.text}</label></li>)}</ul>
      <div className="mt-2 flex gap-2"><input aria-label="New milestone" className={inp} value={ms[v.id] ?? ""} onChange={(e) => setMs({ ...ms, [v.id]: e.target.value })} placeholder="Next step" />
        <button className={small} onClick={() => { const t = (ms[v.id] ?? "").trim(); if (t) { void save(v, { milestones: [...v.milestones, { text: t, done: false }] }); setMs({ ...ms, [v.id]: "" }); } }}>Add</button></div>
      <button className={`${danger} mt-3`} onClick={async () => { await run(() => call("DELETE", `/v1/me/ventures/${v.id}`)); void d.reload(); }}>Delete venture</button></section>))}</div>);
}

export function Credentials() {
  const d = useMine<{ credentials: { code: string; issuer: string; title: string; evidence_url: string; issued_on: string; revoked: boolean; note: string }[] }>("/v1/me/credentials");
  return (<div className="max-w-3xl"><Note>Partner credentials are issued by the partner organisation. Samarthya records them and links to the partner's own evidence. They are not accredited qualifications. Your internal badges are separate and also not accredited.</Note>
    {d.data && !d.data.credentials.length && <p className="mt-4">You have no partner credentials yet.</p>}
    <ul className="mt-4 grid gap-3">{d.data?.credentials.map((c) => <li key={c.code} className="rounded-md border border-ink/10 bg-white p-4"><h3 className="font-semibold">{c.title}{c.revoked ? " (revoked)" : ""}</h3>
      <p>Issued by {c.issuer} on {c.issued_on}</p><p><a className="text-electric-blue underline" href={c.evidence_url} target="_blank" rel="noopener noreferrer">The partner's own record</a> · Verification code <code>{c.code}</code></p></li>)}</ul></div>);
}

type Sw = { from: { title: string }; to: { title: string }; already_shared: string[]; to_add: { tier: string; label: string; note: string | null; free_resources: { title: string; url: string }[] }[]; note: string };
export function CareerSwitch({ roles }: { roles: { slug: string; title: string }[] }) {
  const [a, setA] = useState(""); const [b, setB] = useState(""); const [out, setOut] = useState<Sw | null>(null); const { error, run } = useAction();
  async function go(e: React.FormEvent) { e.preventDefault(); const r = await run(() => call<Sw>("GET", `/v1/tools/career-switch?from=${a}&to=${b}`)); if (r) setOut(r); }
  return (<div className="max-w-3xl"><form onSubmit={go} className="grid gap-3 sm:grid-cols-2">
    <Labeled id="from" label="Where you are now"><select id="from" className={inp} value={a} onChange={(e) => setA(e.target.value)} required><option value="">Choose a role</option>{roles.map((r) => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></Labeled>
    <Labeled id="to" label="Where you want to go"><select id="to" className={inp} value={b} onChange={(e) => setB(e.target.value)} required><option value="">Choose a role</option>{roles.map((r) => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></Labeled>
    <div><button className={btn}>Compare</button></div></form><ErrorText>{error}</ErrorText>
    {!roles.length && <Note>No roles are published yet, so there is nothing to compare.</Note>}
    {out && <div className="mt-6" aria-live="polite"><h2 className="text-xl font-semibold">{out.from.title} → {out.to.title}</h2>
      {out.already_shared.length > 0 && <p className="mt-2">Already shared: {out.already_shared.join(", ")}.</p>}
      <h3 className="mt-4 font-semibold">To add</h3>{!out.to_add.length && <p>The target role lists nothing beyond what you already have.</p>}
      <ul className="mt-2 grid gap-2">{out.to_add.map((g, i) => <li key={i} className="rounded border border-ink/10 bg-white p-3"><strong>{g.label}</strong> <span className="text-sm text-slate">({g.tier.replace("_", " ")})</span>{g.note && <p className="text-sm">{g.note}</p>}
        {g.free_resources.map((r) => <p key={r.url}><a className="text-electric-blue underline" href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a></p>)}</li>)}</ul>
      <p className="mt-3 text-sm text-slate">{out.note}</p></div>}</div>);
}

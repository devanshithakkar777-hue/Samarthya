"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note, small, Tabs } from "@/components/kit/Controls";
import Handle from "./Handle";

type M = { id: number; display_name: string; headline: string; bio: string; kind: string; expertise: string[]; languages: string[]; profile_url: string };
type Mine = M & { status: string };
type Req = { id: number; from?: string; mentor?: string; message: string; status: string; reply?: string | null; contact?: string | null };
const KINDS = ["industry", "alumni", "academic", "research", "entrepreneurship"];

export default function Mentors() {
  const [tab, setTab] = useState("find");
  return (
    <Handle>{() => (<div><Tabs label="Mentors" value={tab} onChange={setTab} tabs={[{ key: "find", label: "Find a mentor" }, { key: "sent", label: "My requests" }, { key: "be", label: "Become a mentor" }, { key: "inbox", label: "Requests to me" }]} />
      {tab === "find" && <Find />}{tab === "sent" && <Sent />}{tab === "be" && <Apply />}{tab === "inbox" && <Inbox />}</div>)}</Handle>
  );
}

function Find() {
  const [kind, setKind] = useState(""); const [q, setQ] = useState("");
  const d = useMine<{ mentors: M[]; note: string }>(`/v1/mentors?${new URLSearchParams({ ...(kind && { kind }), ...(q && { q }) })}`);
  const [open, setOpen] = useState<number | null>(null);
  const [msg, setMsg] = useState(""); const [contact, setContact] = useState(""); const [done, setDone] = useState("");
  const { busy, error, run } = useAction();
  return (
    <div className="grid gap-4">
      <Note>{d.data?.note ?? "Mentors are volunteers, checked against a public profile before they appear."}</Note>
      <div className="flex flex-wrap gap-3"><div><label htmlFor="mq" className="block font-medium">Search</label><input id="mq" className={inp} value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <div><label htmlFor="mk" className="block font-medium">Kind</label><select id="mk" className={inp} value={kind} onChange={(e) => setKind(e.target.value)}><option value="">All</option>{KINDS.map((k) => <option key={k}>{k}</option>)}</select></div></div>
      {done && <p role="status" className="rounded border border-ink/10 bg-white p-3">{done}</p>}
      <ul className="grid gap-4 md:grid-cols-2">{(d.data?.mentors ?? []).map((m) => (
        <li key={m.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5"><h3 className="font-semibold">{m.display_name}</h3><p className="text-sm text-slate">{m.headline} · {m.kind}</p><p className="mt-2 text-sm">{m.bio}</p>
          <p className="mt-1 text-sm text-slate">{[m.expertise.join(", "), m.languages.join(", ")].filter(Boolean).join(" · ")}</p>
          <p className="mt-1 text-sm"><a className="text-electric-blue underline" href={m.profile_url} target="_blank" rel="noopener noreferrer">Public profile<span className="sr-only"> (opens in a new tab)</span></a></p>
          {open === m.id ? (<form className="mt-3 grid gap-3" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call<{ note: string }>("POST", `/v1/mentors/${m.id}/requests`, { message: msg, share_contact: contact || null })); if (r) { setDone(r.note); setOpen(null); setMsg(""); setContact(""); } }}>
            <Labeled id={`m${m.id}`} label="Introduce yourself and say what you would like help with" help="At least 20 characters. No contact details in the message."><textarea id={`m${m.id}`} rows={4} className={inp} required minLength={20} value={msg} onChange={(e) => setMsg(e.target.value)} /></Labeled>
            <Labeled id={`c${m.id}`} label="Contact to share only if they accept (optional)" help="For example an email. Leave blank to keep everything inside Samarthya."><input id={`c${m.id}`} className={inp} value={contact} onChange={(e) => setContact(e.target.value)} /></Labeled>
            <ErrorText>{error}</ErrorText><div className="flex gap-2"><button className={btn} disabled={busy}>Send request</button><button type="button" className={small} onClick={() => setOpen(null)}>Cancel</button></div></form>
          ) : <button className={`${small} mt-3`} onClick={() => setOpen(m.id)}>Ask for guidance</button>}</li>))}</ul>
      {(d.data?.mentors ?? []).length === 0 && <p className="text-slate">No approved mentors yet.</p>}
    </div>
  );
}

function Sent() { const d = useMine<Req[]>("/v1/mentors/requests/sent"); return <ReqList rows={d.data ?? []} who="mentor" empty="You have not asked anyone yet." />; }

function ReqList({ rows, who, empty }: { rows: Req[]; who: "mentor" | "from"; empty: string }) {
  return rows.length === 0 ? <p className="text-slate">{empty}</p> : <ul className="grid gap-3">{rows.map((r) => <li key={r.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{r[who]} <span className="text-sm font-normal text-slate">({r.status})</span></p><p className="mt-1 text-sm">{r.message}</p>{r.reply && <p className="mt-2 text-sm"><strong>Reply:</strong> {r.reply}</p>}{r.contact && <p className="mt-1 text-sm"><strong>Contact shared:</strong> {r.contact}</p>}</li>)}</ul>;
}

function Inbox() {
  const d = useMine<Req[]>("/v1/mentors/requests/received");
  const [reply, setReply] = useState<Record<number, string>>({});
  const { error, run } = useAction();
  if (d.error) return <Note>You can see requests here once you are an approved mentor.</Note>;
  return (<div className="grid gap-3"><ErrorText>{error}</ErrorText>{(d.data ?? []).length === 0 ? <p className="text-slate">No requests yet.</p> : (d.data ?? []).map((r) => (
    <div key={r.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{r.from} <span className="text-sm font-normal text-slate">({r.status})</span></p><p className="mt-1 text-sm">{r.message}</p>{r.contact && <p className="mt-1 text-sm"><strong>They chose to share:</strong> {r.contact}</p>}
      {r.status === "pending" && <div className="mt-3 grid gap-2"><label htmlFor={`rp${r.id}`} className="sr-only">Reply</label><textarea id={`rp${r.id}`} rows={2} className={inp} placeholder="A short reply (no contact details)" value={reply[r.id] ?? ""} onChange={(e) => setReply({ ...reply, [r.id]: e.target.value })} />
        <div className="flex gap-2">{(["accept", "decline"] as const).map((a) => <button key={a} className={small} onClick={async () => { if (await run(() => call("POST", `/v1/mentors/requests/${r.id}/respond`, { action: a, reply: reply[r.id] || null }))) await d.reload(); }}>{a === "accept" ? "Accept" : "Decline"}</button>)}</div></div>}</div>))}</div>);
}

function Apply() {
  const mine = useMine<Mine | null>("/v1/mentors/me");
  const [f, setF] = useState({ display_name: "", headline: "", bio: "", kind: "industry", expertise: "", languages: "English", profile_url: "" });
  const [msg, setMsg] = useState("");
  const { busy, error, run } = useAction();
  const set = (k: string, v: string) => setF({ ...f, [k]: v });
  return (
    <div className="grid max-w-2xl gap-4"><Note>Mentoring is voluntary. A reviewer checks your public profile (for example LinkedIn or a university page) before you appear. Students will only ever see what is on this form. Any edit sends your profile back for review.</Note>
      {mine.data && <p>Your application status: <strong>{mine.data.status}</strong>.</p>}
      <form className="grid gap-4" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call("PUT", "/v1/mentors/me", { ...f, expertise: f.expertise.split(",").map((x) => x.trim()).filter(Boolean), languages: f.languages.split(",").map((x) => x.trim()).filter(Boolean) })); if (r) { setMsg("Submitted for review."); await mine.reload(); } }}>
        <Labeled id="dn" label="Name to show"><input id="dn" className={inp} required value={f.display_name} onChange={(e) => set("display_name", e.target.value)} /></Labeled>
        <Labeled id="hl" label="Headline"><input id="hl" className={inp} required value={f.headline} onChange={(e) => set("headline", e.target.value)} /></Labeled>
        <Labeled id="bi" label="About you and how you can help" help="At least 20 characters. No contact details."><textarea id="bi" rows={4} className={inp} required minLength={20} value={f.bio} onChange={(e) => set("bio", e.target.value)} /></Labeled>
        <Labeled id="kd" label="Kind"><select id="kd" className={inp} value={f.kind} onChange={(e) => set("kind", e.target.value)}>{KINDS.map((k) => <option key={k}>{k}</option>)}</select></Labeled>
        <Labeled id="ex" label="Areas of expertise (comma separated)"><input id="ex" className={inp} value={f.expertise} onChange={(e) => set("expertise", e.target.value)} /></Labeled>
        <Labeled id="lg" label="Languages (comma separated)"><input id="lg" className={inp} value={f.languages} onChange={(e) => set("languages", e.target.value)} /></Labeled>
        <Labeled id="pu" label="Public profile link (https://)"><input id="pu" className={inp} required type="url" value={f.profile_url} onChange={(e) => set("profile_url", e.target.value)} /></Labeled>
        <ErrorText>{error}</ErrorText><div className="flex items-center gap-3"><button className={btn} disabled={busy}>Submit for review</button><span role="status" className="text-sm text-slate">{msg}</span></div></form></div>
  );
}

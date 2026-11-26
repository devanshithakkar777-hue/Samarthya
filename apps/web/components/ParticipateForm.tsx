"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { btn } from "./ui";

const PATHS: [string, string][] = [["mentor", "Mentor students"], ["contribute", "Contribute resources or verify content"], ["institution", "Collaborate as an institution"], ["volunteer", "Volunteer"], ["other", "Something else"]];

export default function ParticipateForm() {
  const [f, setF] = useState({ pathway: "contribute", name: "", organisation: "", contact: "", message: "" });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");
  const [err, setErr] = useState("");
  const set = (k: string, v: string) => setF((p) => ({ ...p, [k]: v }));
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const r = await call<{ message: string }>("POST", "/v1/participate", { ...f, name: f.name || null, organisation: f.organisation || null, message: f.message || null });
      setDone(r.message);
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }
  if (done) return <p role="status" className="rounded-lg bg-white p-6 text-lg">{done}</p>;
  const inp = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-3";
  return (
    <form onSubmit={submit} className="grid max-w-xl gap-4">
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      <div><label htmlFor="p" className="font-semibold">How would you like to help?</label>
        <select id="p" className={inp} value={f.pathway} onChange={(e) => set("pathway", e.target.value)}>{PATHS.map(([v, l]) => (<option key={v} value={v}>{l}</option>))}</select></div>
      <div><label htmlFor="n" className="font-semibold">Your name (optional)</label><input id="n" className={inp} value={f.name} onChange={(e) => set("name", e.target.value)} /></div>
      <div><label htmlFor="o" className="font-semibold">Organisation (optional)</label><input id="o" className={inp} value={f.organisation} onChange={(e) => set("organisation", e.target.value)} /></div>
      <div><label htmlFor="c" className="font-semibold">Your email</label><input id="c" type="email" required className={inp} value={f.contact} onChange={(e) => set("contact", e.target.value)} /></div>
      <div><label htmlFor="m" className="font-semibold">Anything we should know? (optional)</label><textarea id="m" rows={4} maxLength={2000} className={inp} value={f.message} onChange={(e) => set("message", e.target.value)} /></div>
      <p className="text-sm text-slate">We use your details only to reply to this offer. We do not add you to any mailing list.</p>
      <div><button className={btn} disabled={busy}>{busy ? "Sending…" : "Send"}</button></div>
    </form>
  );
}

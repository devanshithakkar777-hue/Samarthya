"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, Note } from "@/components/kit/Controls";

type L = { id: number; label: string | null; show_activity: boolean; show_badges: boolean; show_topics: boolean; expires_on: string; active: boolean };
export default function ParentLinks() {
  const { data, reload } = useMine<{ links: L[]; note: string }>("/v1/me/parent-links");
  const [label, setLabel] = useState("");
  const [act, setAct] = useState(true), [bad, setBad] = useState(true), [top, setTop] = useState(false);
  const [made, setMade] = useState("");
  const { busy, error, run } = useAction();
  async function create(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<{ path: string }>("POST", "/v1/me/parent-links", { label: label || null, show_activity: act, show_badges: bad, show_topics: top }));
    if (r) { setMade(`${window.location.origin}${r.path}`); setLabel(""); void reload(); }
  }
  return (
    <div className="grid max-w-2xl gap-4">
      <Note>{data?.note ?? "Optional. Give a parent or guardian a read-only link to what you choose. It is off unless you make one."}</Note>
      <form onSubmit={create} className="grid gap-2 rounded-md border border-ink/10 bg-white p-4">
        <label className="font-medium" htmlFor="pl-label">Who is it for? (optional)</label><input id="pl-label" className="rounded-md border border-slate/50 px-3 py-2" value={label} onChange={(e) => setLabel(e.target.value)} maxLength={60} />
        <label className="flex gap-2"><input type="checkbox" checked={act} onChange={(e) => setAct(e.target.checked)} />Learning activity (days active)</label>
        <label className="flex gap-2"><input type="checkbox" checked={bad} onChange={(e) => setBad(e.target.checked)} />Milestones earned</label>
        <label className="flex gap-2"><input type="checkbox" checked={top} onChange={(e) => setTop(e.target.checked)} />Topics practised</label>
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Create a 30-day link</button></div>
      </form>
      {made && <div role="status" className="rounded-md border border-electric-blue bg-white p-4"><p className="font-medium">Copy this link now. It will not be shown again.</p><p className="break-all font-mono text-sm">{made}</p></div>}
      <ul className="grid gap-2">{(data?.links ?? []).map((l) => (
        <li key={l.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-ink/10 bg-white p-3"><span>{l.label || "Link"} · {l.active ? `until ${l.expires_on}` : "ended"}</span>
          {l.active && <button className={danger} onClick={async () => { await run(() => call("DELETE", `/v1/me/parent-links/${l.id}`)); void reload(); }}>Cancel link</button>}</li>))}</ul>
    </div>
  );
}

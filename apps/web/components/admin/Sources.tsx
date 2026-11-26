"use client";

import { useEffect, useState } from "react";
import { ApiError, call } from "@/lib/client";
import { btn } from "@/components/ui";

type Src = { id: number; url: string; title: string; publisher: string; kind: string; published_on: string | null };
export const KINDS = ["official", "open_data", "licensed", "third_party"];

export function SourceForm({ onCreated }: { onCreated: (s: Src) => void }) {
  const [f, setF] = useState({ url: "", title: "", publisher: "", kind: "official", published_on: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setF((p) => ({ ...p, [k]: v }));
  async function save() {
    setErr("");
    if (!f.url || !f.title || !f.publisher) { setErr("Link, title and publisher are required."); return; }
    setBusy(true);
    try {
      const s = await call<Src>("POST", "/v1/admin/sources", { ...f, published_on: f.published_on || null });
      onCreated(s); setF({ url: "", title: "", publisher: "", kind: "official", published_on: "" });
    } catch (x) {
      if (x instanceof ApiError && x.status === 409) {
        // that link is already a source: use the existing one instead of failing
        const existing = (await call<Src[]>("GET", "/v1/admin/sources").catch(() => [])).find((s) => s.url === f.url);
        if (existing) { onCreated(existing); setBusy(false); return; }
      }
      setErr((x as Error).message);
    } finally { setBusy(false); }
  }
  const inp = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-2";
  return (
    <div role="group" aria-label="Add a source" className="grid gap-3 rounded-lg border border-ink/10 bg-white p-4">
      <h3 className="font-semibold">Add a source</h3>
      {err && <p role="alert" className="rounded bg-ink p-2 text-arctic-white">{err}</p>}
      <label>Link to the page<input type="url" className={inp} value={f.url} onChange={(e) => set("url", e.target.value)} /></label>
      <label>Page title<input className={inp} value={f.title} onChange={(e) => set("title", e.target.value)} /></label>
      <label>Publisher (who owns it)<input className={inp} value={f.publisher} onChange={(e) => set("publisher", e.target.value)} /></label>
      <label>Kind<select className={inp} value={f.kind} onChange={(e) => set("kind", e.target.value)}>{KINDS.map((k) => (<option key={k}>{k}</option>))}</select></label>
      <label>Published on (optional)<input type="date" className={inp} value={f.published_on} onChange={(e) => set("published_on", e.target.value)} /></label>
      <div><button type="button" onClick={save} className={btn} disabled={busy}>{busy ? "Saving…" : "Save source"}</button></div>
    </div>
  );
}

export default function Sources() {
  const [rows, setRows] = useState<Src[]>([]);
  const [err, setErr] = useState("");
  useEffect(() => { call<Src[]>("GET", "/v1/admin/sources").then(setRows).catch((e: Error) => setErr(e.message)); }, []);
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div><h2 className="mb-3 text-2xl font-semibold">Sources</h2>{err && <p role="alert">{err}</p>}
        <ul className="grid gap-2">{rows.map((s) => (<li key={s.id} className="rounded-lg bg-white p-3 shadow-sm"><span className="text-sm text-slate">#{s.id} · {s.kind}</span><br /><a className="text-electric-blue underline" href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a> <span className="text-slate">{s.publisher}</span></li>))}
          {!rows.length && <li className="text-slate">No sources yet.</li>}</ul></div>
      <SourceForm onCreated={(s) => setRows((r) => [s, ...r])} />
    </div>
  );
}

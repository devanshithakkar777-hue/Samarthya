"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ENTITIES, STATUS_LABEL, labelOf, type EntityConfig, type Field, type Linked } from "@/lib/admin";
import { call } from "@/lib/client";
import { btn } from "@/components/ui";
import FieldInput, { type RefOptions } from "./FieldInput";
import Gate from "./Gate";
import { SourceForm } from "./Sources";

type Row = Record<string, unknown> & { id: number; status?: string; source_id?: number | null; last_verified?: string | null; created_by_id?: number };
type Src = { id: number; title: string; publisher: string };

function useRefs(fields: Field[]) {
  const [refs, setRefs] = useState<RefOptions>({});
  useEffect(() => {
    const names = Array.from(new Set(fields.filter((f) => f.type === "ref").map((f) => f.ref!)));
    names.forEach((n) => {
      const cfg = ENTITIES[n];
      call<Row[]>("GET", `/v1/admin/${n}`).then((rows) =>
        setRefs((p) => ({ ...p, [n]: rows.map((r) => ({ id: r.id, label: `${labelOf(cfg, r)}${r.status && r.status !== "published" ? ` (${r.status})` : ""}` })) }))).catch(() => {});
    });
  }, [fields]);
  return refs;
}

function LinkedPanel({ parentId, spec, refs }: { parentId: number; spec: Linked; refs: RefOptions }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [err, setErr] = useState("");
  const load = useCallback(() => {
    call<Row[]>("GET", `/v1/admin/${spec.entity}`).then((r) => setRows(r.filter((x) => x[spec.fk] === parentId))).catch((e: Error) => setErr(e.message));
  }, [spec, parentId]);
  useEffect(load, [load]);
  const own = useRefs(spec.fields);
  const all = { ...refs, ...own };
  const text = (r: Row) => spec.summary.map((k) => { const f = spec.fields.find((x) => x.name === k); const v = r[k];
    if (f?.type === "ref") return all[f.ref!]?.find((o) => o.id === v)?.label ?? String(v); return String(v ?? ""); }).filter(Boolean).join(" · ");
  async function add(e: React.FormEvent) {
    e.preventDefault(); setErr("");
    try { await call("POST", `/v1/admin/${spec.entity}`, { ...draft, [spec.fk]: parentId }); setDraft({}); load(); } catch (x) { setErr((x as Error).message); }
  }
  async function remove(id: number) {
    try { await call("DELETE", `/v1/admin/${spec.entity}/${id}`); load(); } catch (x) { setErr((x as Error).message); }
  }
  return (
    <section className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
      <h3 className="text-lg font-semibold">{spec.title}</h3>
      {err && <p role="alert" className="mt-2 rounded bg-ink p-2 text-arctic-white">{err}</p>}
      <ul className="mt-3 grid gap-2">{rows.map((r) => (
        <li key={r.id} className="flex items-center justify-between gap-3 rounded bg-arctic-white p-2"><span>{text(r)}</span><button className="text-sm underline" onClick={() => remove(r.id)}>Remove</button></li>))}
        {!rows.length && <li className="text-slate">None yet.</li>}</ul>
      <form onSubmit={add} className="mt-4 grid gap-3 border-t border-ink/10 pt-4">
        {spec.fields.map((f) => (<FieldInput key={f.name} f={f} value={draft[f.name]} onChange={(v) => setDraft((p) => ({ ...p, [f.name]: v }))} refs={all} />))}
        <div><button className={btn}>Add</button></div>
      </form>
    </section>
  );
}

function Editor({ cfg, id, role }: { cfg: EntityConfig; id: string; role: string }) {
  const router = useRouter();
  const isNew = id === "new";
  const [row, setRow] = useState<Row | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [sources, setSources] = useState<Src[]>([]);
  const [showSrc, setShowSrc] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [me, setMe] = useState<number | null>(null);
  const reviewer = role === "reviewer" || role === "admin";

  const fields = useMemo<Field[]>(() => cfg.fields, [cfg]);
  const refs = useRefs(fields);

  useEffect(() => {
    call<Src[]>("GET", "/v1/admin/sources").then(setSources).catch(() => {});
    call<{ id?: number }>("GET", "/v1/me").then((u) => setMe(u.id ?? null)).catch(() => {});
    if (!isNew) call<Row>("GET", `/v1/admin/${cfg.key}/${id}`).then((r) => { setRow(r); setForm(r); }).catch((e: Error) => setErr(e.message));
  }, [cfg.key, id, isNew]);

  const set = (k: string, v: unknown) => setForm((p) => ({ ...p, [k]: v }));
  const editable = new Set([...fields.map((f) => f.name), "source_id", "last_verified"]);

  async function save(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setMsg(""); setBusy(true);
    const body: Record<string, unknown> = {};
    editable.forEach((k) => { const v = form[k]; if (v !== undefined && v !== "" && v !== null) body[k] = v; });
    for (const f of fields) {
      if (f.type === "json" && typeof body[f.name] === "string") {
        try { body[f.name] = JSON.parse(body[f.name] as string); } catch { setErr(`${f.label} is not valid JSON. Check commas and quotes.`); setBusy(false); return; }
      }
      if (f.type === "lines" && Array.isArray(body[f.name])) body[f.name] = (body[f.name] as string[]).map((x) => x.trim()).filter(Boolean);
    }
    try {
      if (isNew) { const r = await call<Row>("POST", `/v1/admin/${cfg.key}`, body); router.replace(`/admin/${cfg.key}/${r.id}`); }
      else { const r = await call<Row>("PATCH", `/v1/admin/${cfg.key}/${id}`, body); setRow(r); setForm(r); setMsg("Saved."); }
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }
  async function act(action: string) {
    setErr(""); setMsg("");
    const note = action === "reject" ? window.prompt("What needs to change? The author will see this.") ?? "" : undefined;
    if (action === "reject" && !note) return;
    try { const r = await call<Row>("POST", `/v1/admin/${cfg.key}/${id}/${action}`, note ? { note } : {}); setRow(r); setForm(r); setMsg(`Done: ${action}.`); }
    catch (x) { setErr((x as Error).message); }
  }
  async function del() {
    if (!window.confirm("Delete this draft? This cannot be undone.")) return;
    try { await call("DELETE", `/v1/admin/${cfg.key}/${id}`); router.replace(`/admin/${cfg.key}`); } catch (x) { setErr((x as Error).message); }
  }

  const status = row?.status;
  const ownWork = me !== null && row?.created_by_id === me;
  return (
    <div className="grid max-w-3xl gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-2xl font-semibold">{isNew ? `New ${cfg.singular.toLowerCase()}` : labelOf(cfg, row ?? { id: Number(id) })}</h2>
        {status && <span className="rounded bg-midnight-navy px-2 py-0.5 text-sm text-arctic-white">{STATUS_LABEL[status] ?? status}</span>}
      </div>
      {cfg.hint && <p className="text-slate">{cfg.hint}</p>}
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      {msg && <p role="status" className="rounded bg-white p-3">{msg}</p>}

      <form onSubmit={save} className="grid gap-4 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
        {fields.map((f) => (<FieldInput key={f.name} f={f} value={form[f.name]} onChange={(v) => set(f.name, v)} refs={refs} />))}
        {cfg.sourced && (
          <fieldset className="grid gap-3 rounded border border-ink/10 p-4">
            <legend className="px-1 font-semibold">Where does this come from?</legend>
            <label>Source (required to submit)
              <select className="mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-2" value={String(form.source_id ?? "")} onChange={(e) => set("source_id", e.target.value ? Number(e.target.value) : null)}>
                <option value="">Choose a source…</option>{sources.map((s) => (<option key={s.id} value={s.id}>{s.title}, {s.publisher}</option>))}</select></label>
            <button type="button" className="justify-self-start text-electric-blue underline" onClick={() => setShowSrc((v) => !v)}>{showSrc ? "Hide" : "Source not listed? Add one"}</button>
            {showSrc && <SourceForm onCreated={(s) => { setSources((p) => [s as Src, ...p]); set("source_id", s.id); setShowSrc(false); }} />}
            <FieldInput f={{ name: "last_verified", label: "Date you checked this against the source", type: "date" }} value={form.last_verified} onChange={(v) => set("last_verified", v)} refs={{}} />
          </fieldset>
        )}
        <div className="flex flex-wrap gap-3">
          <button className={btn} disabled={busy}>{busy ? "Saving…" : isNew ? "Create draft" : "Save changes"}</button>
          {!isNew && <Link href={`/admin/${cfg.key}`} className="px-3 py-3 underline">Back to list</Link>}
        </div>
      </form>

      {!isNew && (
        <section aria-labelledby="flow" className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
          <h3 id="flow" className="text-lg font-semibold">Review steps</h3>
          <div className="mt-3 flex flex-wrap gap-3">
            {status === "draft" && <button className={btn} onClick={() => act("submit")}>Send for review</button>}
            {status === "in_review" && reviewer && !(ownWork) && (<><button className={btn} onClick={() => act("approve")}>Approve and publish</button><button className="rounded-md border border-ink px-5 py-3" onClick={() => act("reject")}>Send back with a note</button></>)}
            {status === "in_review" && (ownWork || !reviewer) && <p className="text-slate">Waiting for a different reviewer. You cannot approve your own work.</p>}
            {status === "published" && reviewer && (<><button className="rounded-md border border-ink px-5 py-3" onClick={() => act("verify")}>I re-checked this today</button><button className="rounded-md border border-ink px-5 py-3" onClick={() => act("unpublish")}>Unpublish</button></>)}
            {status === "draft" && <button className="rounded-md border border-ink px-5 py-3" onClick={del}>Delete draft</button>}
          </div>
        </section>
      )}

      {!isNew && cfg.linked?.map((l) => (<LinkedPanel key={l.entity} parentId={Number(id)} spec={l} refs={refs} />))}
    </div>
  );
}

export default function EntityEditor({ entity, id }: { entity: string; id: string }) {
  const cfg = ENTITIES[entity];
  return <Gate>{(role) => (cfg ? <Editor cfg={cfg} id={id} role={role} /> : <p>Unknown content type.</p>)}</Gate>;
}

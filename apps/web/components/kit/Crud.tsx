"use client";

import { useState, type ReactNode } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, inp, Labeled, small } from "./Controls";

export type CField = {
  name: string; label: string; help?: string; required?: boolean;
  type?: "text" | "textarea" | "number" | "date" | "select" | "bool" | "lines" | "evidence";
  options?: string[]; rows?: number;
};
type Row = Record<string, unknown> & { id: number };

const toForm = (fields: CField[], row?: Row) => {
  const f: Record<string, unknown> = {};
  for (const x of fields) {
    const v = row?.[x.name];
    if (x.type === "lines") f[x.name] = Array.isArray(v) ? (v as string[]).join("\n") : "";
    else if (x.type === "evidence") f[x.name] = Array.isArray(v) ? (v as { kind: string; url: string }[]).map((e) => `${e.kind} ${e.url}`).join("\n") : "";
    else if (x.type === "bool") f[x.name] = !!v;
    else f[x.name] = v ?? "";
  }
  return f;
};
const toBody = (fields: CField[], form: Record<string, unknown>, extra: Record<string, unknown>) => {
  const b: Record<string, unknown> = { ...extra };
  for (const x of fields) {
    const v = form[x.name];
    if (x.type === "lines") b[x.name] = String(v ?? "").split("\n").map((s) => s.trim()).filter(Boolean);
    else if (x.type === "evidence") b[x.name] = String(v ?? "").split("\n").map((s) => s.trim()).filter(Boolean).map((l) => { const [kind, ...rest] = l.split(/\s+/); return { kind, url: rest.join(" ") }; });
    else if (x.type === "number") b[x.name] = v === "" || v == null ? null : Number(v);
    else if (x.type === "date") b[x.name] = v === "" ? null : v;
    else if (x.type === "bool") b[x.name] = !!v;
    else b[x.name] = v === "" ? null : v;
  }
  return b;
};

/** A small create/edit/delete list for one of the student's own resources. */
export default function Crud({ path, listKey, fields, noun, render, extra = {}, empty, onChange, filter }: {
  filter?: (r: Row) => boolean;
  path: string; listKey?: string; fields: CField[]; noun: string; render: (r: Row) => ReactNode; extra?: Record<string, unknown>; empty?: string; onChange?: () => void;
}) {
  const { data, error, reload, loading } = useMine<unknown>(path);
  const allRows: Row[] = (listKey ? (data as Record<string, Row[]> | null)?.[listKey] : (data as Row[] | null)) ?? [];
  const rows = filter ? allRows.filter(filter) : allRows;
  const [editing, setEditing] = useState<Row | "new" | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const { busy, error: err, run, setError } = useAction();

  function open(r: Row | "new") { setForm(toForm(fields, r === "new" ? undefined : r)); setEditing(r); setError(""); }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    const body = toBody(fields, form, extra);
    const ok = await run(() => editing === "new" ? call("POST", path, body) : call("PUT", `${path}/${(editing as Row).id}`, body));
    if (ok !== undefined) { setEditing(null); await reload(); onChange?.(); }
  }
  async function remove(r: Row) {
    if (!window.confirm(`Delete this ${noun}? This cannot be undone.`)) return;
    const ok = await run(() => call("DELETE", `${path}/${r.id}`));
    if (ok !== undefined) { await reload(); onChange?.(); }
  }

  return (
    <div>
      <ErrorText>{error}</ErrorText>
      {editing === null ? (
        <button className={btn} onClick={() => open("new")}>Add {noun}</button>
      ) : (
        <form onSubmit={save} className="grid gap-4 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
          <h3 className="text-lg font-semibold">{editing === "new" ? `Add ${noun}` : `Edit ${noun}`}</h3>
          {fields.map((f) => {
            const id = `crud-${f.name}`; const v = form[f.name]; const set = (x: unknown) => setForm({ ...form, [f.name]: x });
            let c: ReactNode;
            if (f.type === "textarea" || f.type === "lines" || f.type === "evidence") c = <textarea id={id} rows={f.rows ?? 4} className={inp} value={String(v ?? "")} onChange={(e) => set(e.target.value)} required={f.required} />;
            else if (f.type === "select") c = <select id={id} className={inp} value={String(v ?? "")} onChange={(e) => set(e.target.value)} required={f.required}><option value="">Choose…</option>{f.options!.map((o) => <option key={o}>{o}</option>)}</select>;
            else if (f.type === "bool") c = <input id={id} type="checkbox" className="ml-2 h-5 w-5 align-middle accent-electric-blue" checked={!!v} onChange={(e) => set(e.target.checked)} />;
            else if (f.type === "date") c = <input id={id} type="date" className={inp} value={String(v ?? "").slice(0, 10)} onChange={(e) => set(e.target.value)} required={f.required} />;
            else c = <input id={id} inputMode={f.type === "number" ? "numeric" : undefined} className={inp} value={String(v ?? "")} onChange={(e) => set(e.target.value)} required={f.required} />;
            return <Labeled key={f.name} id={id} label={f.label + (f.required ? " (required)" : "")} help={f.help}>{c}</Labeled>;
          })}
          <ErrorText>{err}</ErrorText>
          <div className="flex gap-3"><button className={btn} disabled={busy}>{busy ? "Saving…" : "Save"}</button>
            <button type="button" className={small} onClick={() => setEditing(null)}>Cancel</button></div>
        </form>
      )}
      {loading && !data ? <p className="mt-4 text-slate" role="status">Loading…</p> : rows.length === 0 && editing === null ? (
        <p className="mt-4 text-slate">{empty ?? `No ${noun}s yet.`}</p>
      ) : (
        <ul className="mt-4 grid gap-3">
          {rows.map((r) => (
            <li key={r.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4">
              {render(r)}
              <div className="mt-3 flex gap-2"><button className={small} onClick={() => open(r)}>Edit</button><button className={danger} onClick={() => remove(r)}>Delete</button></div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

"use client";

import type { Field } from "@/lib/admin";

export type RefOptions = Record<string, { id: number; label: string }[]>;
const inp = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-2";

export default function FieldInput({ f, value, onChange, refs }: { f: Field; value: unknown; onChange: (v: unknown) => void; refs: RefOptions }) {
  const id = `f-${f.name}`;
  const v = value ?? "";
  let control;
  if (f.type === "textarea") control = <textarea id={id} rows={4} className={inp} value={String(v)} onChange={(e) => onChange(e.target.value)} />;
  else if (f.type === "json") control = <textarea id={id} rows={10} spellCheck={false} className={`${inp} font-mono text-sm`} value={typeof value === "string" ? value : value == null ? "" : JSON.stringify(value, null, 2)} onChange={(e) => onChange(e.target.value)} />;
  else if (f.type === "lines") control = <textarea id={id} rows={4} className={inp} value={Array.isArray(value) ? (value as string[]).join("\n") : String(v)} onChange={(e) => onChange(e.target.value.split("\n"))} />;
  else if (f.type === "bool") control = <input id={id} type="checkbox" className="ml-2 h-5 w-5 align-middle accent-electric-blue" checked={!!value} onChange={(e) => onChange(e.target.checked)} />;
  else if (f.type === "select") control = (<select id={id} className={inp} value={String(v)} onChange={(e) => onChange(e.target.value)}><option value="">Choose…</option>{f.options!.map((o) => (<option key={o}>{o}</option>))}</select>);
  else if (f.type === "ref") control = (<select id={id} className={inp} value={String(v)} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}><option value="">Choose…</option>{(refs[f.ref!] ?? []).map((o) => (<option key={o.id} value={o.id}>{o.label}</option>))}</select>);
  else if (f.type === "number") control = <input id={id} inputMode="numeric" className={inp} value={String(v)} onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))} />;
  else if (f.type === "date") control = <input id={id} type="date" className={inp} value={String(v).slice(0, 10)} onChange={(e) => onChange(e.target.value || null)} />;
  else control = <input id={id} className={inp} value={String(v)} onChange={(e) => onChange(e.target.value)} />;
  return (
    <div>
      <label htmlFor={id} className="font-medium">{f.label}{f.required && <span className="text-slate"> (required)</span>}</label>
      {control}
      {f.help && <p className="text-sm text-slate">{f.help}</p>}
    </div>
  );
}

"use client";

import type { ReactNode } from "react";

export const inp = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-2";
export const small = "inline-flex items-center rounded-md border border-electric-blue px-3 py-1.5 text-sm font-medium text-electric-blue hover:bg-electric-blue hover:text-arctic-white disabled:opacity-60";
export const danger = "inline-flex items-center rounded-md border border-ink px-3 py-1.5 text-sm font-medium text-ink hover:bg-ink hover:text-arctic-white disabled:opacity-60";

export function Labeled({ id, label, help, children }: { id: string; label: string; help?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="font-medium">{label}</label>
      {children}
      {help && <p className="text-sm text-slate">{help}</p>}
    </div>
  );
}

export function ErrorText({ children }: { children?: string }) {
  return children ? <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{children}</p> : null;
}

export function Note({ children }: { children: ReactNode }) {
  return <p className="rounded-md border border-ink/10 bg-white p-3 text-sm text-slate">{children}</p>;
}

export function Tabs({ tabs, value, onChange, label }: { tabs: { key: string; label: string }[]; value: string; onChange: (k: string) => void; label: string }) {
  return (
    <div role="tablist" aria-label={label} className="mb-5 flex flex-wrap gap-2">
      {tabs.map((t) => (
        <button key={t.key} role="tab" aria-selected={value === t.key} onClick={() => onChange(t.key)}
          className={`rounded-md px-4 py-2 text-sm font-medium ${value === t.key ? "bg-electric-blue text-arctic-white" : "border border-ink/20 bg-white text-ink hover:border-electric-blue"}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

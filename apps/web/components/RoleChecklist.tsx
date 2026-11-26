"use client";

import Link from "next/link";
import { useState } from "react";
import { useStudent } from "@/lib/student";
import type { RoleDetail } from "@/lib/types";

const TIERS: { key: keyof RoleDetail["requirements"]; title: string; hint: string }[] = [
  { key: "mandatory", title: "Required", hint: "Employers or regulations require these." },
  { key: "common_preference", title: "Commonly preferred", hint: "Often listed, though not always required." },
  { key: "recommended", title: "Recommended", hint: "Helpful preparation we suggest." },
  { key: "differentiator", title: "Stand-out extras", hint: "Not expected, but they set you apart." },
];

export default function RoleChecklist({ requirements }: { requirements: RoleDetail["requirements"] }) {
  const { completed, setRequirement } = useStudent();
  const [err, setErr] = useState("");
  const toggle = async (id: number, done: boolean) => {
    setErr("");
    try { await setRequirement(id, done); } catch { setErr("We could not save that tick. Please try again."); }
  };
  const total = TIERS.reduce((n, t) => n + requirements[t.key].length, 0);
  if (!total) return <p className="text-slate">No requirements are published for this role yet.</p>;
  return (
    <div className="grid gap-6">
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      {TIERS.map((t) => requirements[t.key].length > 0 && (
        <fieldset key={t.key} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5">
          <legend className="px-2 text-lg font-semibold">{t.title}</legend>
          <p className="mb-3 text-sm text-slate">{t.hint}</p>
          <ul className="grid gap-2">
            {requirements[t.key].map((q) => (
              <li key={q.id} className="flex items-start gap-3">
                <input id={`req-${q.id}`} type="checkbox" className="mt-1 h-5 w-5 accent-electric-blue" checked={completed.includes(q.id)} onChange={(e) => toggle(q.id, e.target.checked)} />
                <label htmlFor={`req-${q.id}`}>
                  {q.label}
                  {q.note && <span className="block text-sm text-slate">{q.note}</span>}
                  {q.skill && <Link href={`/skills/${q.skill.slug}`} className="text-sm text-electric-blue underline">Learn {q.skill.name}</Link>}
                </label>
              </li>
            ))}
          </ul>
        </fieldset>
      ))}
      <p className="text-sm text-slate">Ticks are saved on this device. <Link href="/signin" className="text-electric-blue underline">Sign in</Link> to keep them across devices.</p>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useStudent } from "@/lib/student";
import type { FitItem } from "@/lib/types";
import { Empty, btn } from "./ui";

export default function Dashboard() {
  const { ready, user, hasProfile, loadFit, completed, deleteAccount, clearLocal } = useStudent();
  const [items, setItems] = useState<FitItem[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => { if (ready && hasProfile) loadFit("readiness").then(setItems).catch(() => setMsg("Could not load your progress right now.")); }, [ready, hasProfile, loadFit, completed]);

  if (!ready) return <p role="status">Loading…</p>;
  if (!hasProfile) return <Empty title="Nothing here yet"><Link href="/start" className={`${btn} mt-4`}>Find my path</Link></Empty>;

  const next = items.flatMap((i) => i.readiness.outstanding.slice(0, 1).map((o) => ({ role: i.role, o }))).slice(0, 5);
  return (
    <div className="grid gap-8">
      {msg && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{msg}</p>}
      <section aria-labelledby="next">
        <h2 id="next" className="text-xl font-semibold">Your next steps</h2>
        {next.length ? (
          <ul className="mt-3 grid gap-3">
            {next.map(({ role, o }) => (
              <li key={`${role.id}-${o.id}`} className="rounded-lg bg-white p-4 shadow-sm">
                {o.label} <span className="text-slate">for </span><Link className="text-electric-blue underline" href={`/roles/${role.slug}`}>{role.title}</Link>
              </li>
            ))}
          </ul>
        ) : <p className="mt-2 text-slate">No open steps right now. Browse more careers to add more.</p>}
        <div className="mt-4 flex gap-3"><Link className={btn} href="/results">See all my options</Link></div>
      </section>
      <section aria-labelledby="data" className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
        <h2 id="data" className="text-xl font-semibold">Your data</h2>
        {user ? (
          <div className="mt-3 flex flex-wrap gap-3">
            <Link href="/privacy#export" className="text-electric-blue underline">Download or delete everything</Link>
          </div>
        ) : (
          <div className="mt-3 grid gap-3">
            <p className="text-slate">Your answers are stored only on this device.</p>
            <div className="flex flex-wrap gap-3">
              <Link href="/signin" className={btn}>Save to an account</Link>
              <button className="rounded-md border border-slate px-5 py-3" onClick={() => { clearLocal(); }}>Clear data on this device</button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

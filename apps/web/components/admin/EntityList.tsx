"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ENTITIES, STATUS_LABEL, labelOf } from "@/lib/admin";
import { call } from "@/lib/client";
import { btn } from "@/components/ui";
import Gate from "./Gate";
import Sources from "./Sources";

type Row = Record<string, unknown> & { id: number; status?: string };

function List({ entity }: { entity: string }) {
  const cfg = ENTITIES[entity];
  const [rows, setRows] = useState<Row[] | null>(null);
  const [status, setStatus] = useState("");
  const [err, setErr] = useState("");
  useEffect(() => {
    if (!cfg) return;
    setRows(null);
    call<Row[]>("GET", `/v1/admin/${entity}${status ? `?status=${status}` : ""}`).then(setRows).catch((e: Error) => setErr(e.message));
  }, [entity, status, cfg]);
  if (!cfg) return <p>Unknown content type.</p>;
  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-4">
        <h2 className="text-2xl font-semibold">{cfg.plural}</h2>
        <label className="ml-auto text-sm">Show <select className="ml-1 rounded border border-slate/50 bg-white px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">all</option><option value="draft">drafts</option><option value="in_review">in review</option><option value="published">published</option></select></label>
        <Link className={btn} href={`/admin/${entity}/new`}>New {cfg.singular.toLowerCase()}</Link>
      </div>
      {cfg.hint && <p className="mb-4 max-w-3xl text-slate">{cfg.hint}</p>}
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      {rows === null && !err ? <p role="status">Loading…</p> : rows?.length ? (
        <ul className="grid gap-2">{rows.map((r) => (
          <li key={r.id} className="flex items-center justify-between rounded-lg bg-white p-3 shadow-sm">
            <Link className="text-electric-blue underline" href={`/admin/${entity}/${r.id}`}>{labelOf(cfg, r)}</Link>
            <span className="rounded bg-midnight-navy px-2 py-0.5 text-sm text-arctic-white">{STATUS_LABEL[r.status ?? ""] ?? r.status}</span>
          </li>))}</ul>
      ) : rows ? <p className="text-slate">Nothing here yet.</p> : null}
    </div>
  );
}
export default function EntityList({ entity }: { entity: string }) {
  return <Gate>{() => (entity === "sources" ? <Sources /> : <List entity={entity} />)}</Gate>;
}

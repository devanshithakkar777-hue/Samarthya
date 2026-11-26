"use client";

import Link from "next/link";
import { useState } from "react";

type N = { slug: string; headline: string; category: string; date: string };
type E = { from: string; to: string; because: string[]; strength: number };
export default function ImpactMap({ nodes, edges, note }: { nodes: N[]; edges: E[]; note: string }) {
  const [sel, setSel] = useState<string | null>(null);
  const R = 200, C = 240;
  const pos = Object.fromEntries(nodes.map((n, i) => [n.slug, [C + R * Math.cos((2 * Math.PI * i) / Math.max(nodes.length, 1)), C + R * Math.sin((2 * Math.PI * i) / Math.max(nodes.length, 1))]]));
  const linked = (slug: string) => edges.filter((e) => e.from === slug || e.to === slug);
  const cur = sel ? nodes.find((n) => n.slug === sel) : null;
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <p className="mb-2 text-sm text-slate">{note}</p>
        <svg viewBox="0 0 480 480" role="img" aria-label="Map of world briefs joined by shared topics. The list beside it has the same information." className="w-full max-w-lg rounded-lg bg-deep-space">
          {edges.map((e, i) => { const a = pos[e.from], b = pos[e.to]; const on = sel && (e.from === sel || e.to === sel); return a && b ? <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={on ? "#36B9E9" : "#A9C8E8"} strokeOpacity={on ? 0.9 : 0.25} strokeWidth={on ? 2 : 1} /> : null; })}
          {nodes.map((n) => <circle key={n.slug} cx={pos[n.slug][0]} cy={pos[n.slug][1]} r={sel === n.slug ? 9 : 6} fill={sel === n.slug ? "#36B9E9" : "#176BCE"} stroke="#F2F6FC" strokeWidth={1} />)}
        </svg>
      </div>
      <div>
        <ul className="grid max-h-[28rem] gap-1 overflow-auto">{nodes.map((n) => (
          <li key={n.slug}><button type="button" aria-pressed={sel === n.slug} onClick={() => setSel(sel === n.slug ? null : n.slug)} className={`w-full rounded-md border px-3 py-2 text-left text-sm ${sel === n.slug ? "border-electric-blue bg-ice-blue/40" : "border-ink/10 bg-white"}`}>
            <span className="font-medium">{n.headline}</span> <span className="text-slate">· {n.category} · {n.date}</span></button></li>))}</ul>
        {cur && <div className="mt-3 rounded-md border border-ink/10 bg-white p-3" aria-live="polite"><p className="font-medium"><Link className="text-electric-blue underline" href={`/world/briefs/${cur.slug}`}>Open the brief</Link></p>
          {linked(cur.slug).length === 0 ? <p className="text-sm text-slate">No other brief shares a topic with this one yet.</p> : <ul className="mt-1 list-disc pl-5 text-sm">{linked(cur.slug).map((e, i) => { const o = nodes.find((n) => n.slug === (e.from === cur.slug ? e.to : e.from)); return <li key={i}>{o?.headline} (shared: {e.because.join(", ")})</li>; })}</ul>}</div>}
      </div>
    </div>
  );
}

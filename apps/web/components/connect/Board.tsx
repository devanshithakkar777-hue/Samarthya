"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn, fmtDate } from "@/components/ui";
import { ErrorText, inp, Labeled, small } from "@/components/kit/Controls";
import CrisisBox, { type Crisis } from "@/components/live/CrisisBox";
import Handle from "./Handle";

type P = { id: number; title: string; author: string; created_at: string; replies: number };

export default function Board({ board, name }: { board: string; name: string }) {
  const [offset, setOffset] = useState(0);
  const list = useMine<P[]>(`/v1/community/boards/${board}/posts?offset=${offset}`);
  const [t, setT] = useState(""); const [b, setB] = useState("");
  const [care, setCare] = useState<Crisis | null>(null);
  const { busy, error, run } = useAction();
  return (
    <Handle>{() => (<div className="grid max-w-3xl gap-6">
      <form className="grid gap-3 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5" onSubmit={async (e) => {
        e.preventDefault(); const r = await run(() => call<{ id: number; care?: string; resources?: Crisis["resources"] }>("POST", `/v1/community/boards/${board}/posts`, { title: t, body: b }));
        if (r) { setT(""); setB(""); setCare(r.resources ? { message: r.care ?? "", resources: r.resources } : null); await list.reload(); } }}>
        <h2 className="text-lg font-semibold">Start a conversation in {name}</h2>
        <Labeled id="pt" label="Title"><input id="pt" className={inp} required minLength={3} maxLength={200} value={t} onChange={(e) => setT(e.target.value)} /></Labeled>
        <Labeled id="pb" label="Message" help="No phone numbers, emails or social handles."><textarea id="pb" rows={4} className={inp} required minLength={3} maxLength={4000} value={b} onChange={(e) => setB(e.target.value)} /></Labeled>
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Post</button></div></form>
      {care && <CrisisBox c={care} />}
      <ul className="grid gap-3">{(list.data ?? []).map((p) => <li key={p.id} className="rounded-md border border-ink/10 bg-white p-4"><h3 className="font-semibold"><Link className="text-electric-blue underline" href={`/connect/posts/${p.id}`}>{p.title}</Link></h3><p className="text-sm text-slate">{p.author} · {fmtDate(p.created_at)} · {p.replies} repl{p.replies === 1 ? "y" : "ies"}</p></li>)}</ul>
      {(list.data ?? []).length === 0 && <p className="text-slate">Nothing here yet. Be the first.</p>}
      <div className="flex gap-3">{offset > 0 && <button className={small} onClick={() => setOffset(Math.max(0, offset - 30))}>Newer</button>}{(list.data ?? []).length === 30 && <button className={small} onClick={() => setOffset(offset + 30)}>Older</button>}</div>
    </div>)}</Handle>
  );
}

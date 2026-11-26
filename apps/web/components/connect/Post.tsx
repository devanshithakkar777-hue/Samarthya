"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn, fmtDate } from "@/components/ui";
import { danger, ErrorText, inp, small } from "@/components/kit/Controls";
import CrisisBox, { type Crisis } from "@/components/live/CrisisBox";
import Handle from "./Handle";

type R = { id: number; body: string; author: string; created_at: string };
type P = { id: number; board: string; title: string; body: string; author: string; created_at: string; replies_list: R[] };

export default function Post({ id }: { id: string }) {
  const router = useRouter();
  const p = useMine<P>(`/v1/community/posts/${id}`);
  const [body, setBody] = useState("");
  const [care, setCare] = useState<Crisis | null>(null);
  const [note, setNote] = useState("");
  const { busy, error, run } = useAction();
  async function report(kind: "post" | "reply", target: number) {
    const reason = window.prompt("What is wrong with this? (a short reason)");
    if (!reason || reason.trim().length < 3) return;
    const r = await run(() => call<{ note: string }>("POST", "/v1/community/reports", { kind, target_id: target, reason }));
    if (r) setNote(r.note);
  }
  if (p.error) return <ErrorText>{p.error}</ErrorText>;
  return (
    <Handle>{(me) => !p.data ? <p role="status">Loading…</p> : (<div className="max-w-3xl">
      <article className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5"><h2 className="text-xl font-semibold">{p.data.title}</h2><p className="text-sm text-slate">{p.data.author} · {fmtDate(p.data.created_at)}</p><p className="mt-3 whitespace-pre-line">{p.data.body}</p>
        <div className="mt-3 flex gap-2"><button className={small} onClick={() => report("post", p.data!.id)}>Report</button>{p.data.author === me && <button className={danger} onClick={async () => { if (window.confirm("Delete this post and its replies?")) { await call("DELETE", `/v1/community/posts/${id}`); router.push(`/connect/boards/${p.data!.board}`); } }}>Delete</button>}</div></article>
      {note && <p role="status" className="mt-3 rounded border border-ink/10 bg-white p-2 text-sm">{note}</p>}
      <ul className="mt-5 grid gap-3">{p.data.replies_list.map((r) => <li key={r.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="text-sm text-slate">{r.author} · {fmtDate(r.created_at)}</p><p className="mt-1 whitespace-pre-line">{r.body}</p>
        <div className="mt-2 flex gap-2"><button className={small} onClick={() => report("reply", r.id)}>Report</button>{r.author === me && <button className={danger} onClick={async () => { await call("DELETE", `/v1/community/replies/${r.id}`); await p.reload(); }}>Delete</button>}</div></li>)}</ul>
      {care && <div className="mt-4"><CrisisBox c={care} /></div>}
      <form className="mt-6 grid gap-3" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call<{ care?: string; resources?: Crisis["resources"] }>("POST", `/v1/community/posts/${id}/replies`, { body })); if (r) { setBody(""); setCare(r.resources ? { message: r.care ?? "", resources: r.resources } : null); await p.reload(); } }}>
        <label htmlFor="rb" className="font-medium">Reply</label><textarea id="rb" rows={3} className={inp} required maxLength={2000} value={body} onChange={(e) => setBody(e.target.value)} />
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Reply</button></div></form></div>)}</Handle>
  );
}

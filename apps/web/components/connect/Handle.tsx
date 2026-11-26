"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";
import type { ReactNode } from "react";

type Me = { handle: string | null; guidelines: string[] };

/** Community identity is a chosen handle, never an email or a real name. Children render once a handle exists. */
export default function Handle({ children }: { children: (handle: string) => ReactNode }) {
  const me = useMine<Me>("/v1/community/me");
  const [h, setH] = useState("");
  const { busy, error, run } = useAction();
  if (!me.data) return <p role="status">Loading…</p>;
  if (!me.data.handle) return (
    <form className="grid max-w-xl gap-4 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5" onSubmit={async (e) => { e.preventDefault(); if (await run(() => call("PUT", "/v1/community/me", { handle: h }))) await me.reload(); }}>
      <h2 className="text-xl font-semibold">Choose a handle</h2>
      <Note>Others see only this handle, never your name or email. Pick something that does not identify you. You cannot share phone numbers, emails or social accounts here.</Note>
      <Labeled id="hd" label="Handle" help="3 to 30 characters: lowercase letters, numbers and underscores."><input id="hd" className={inp} required value={h} onChange={(e) => setH(e.target.value)} autoComplete="off" /></Labeled>
      <ul className="list-disc pl-5 text-sm text-slate">{me.data.guidelines.map((g) => <li key={g}>{g}</li>)}</ul>
      <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy}>Join the community</button></div></form>);
  return <>{children(me.data.handle)}</>;
}

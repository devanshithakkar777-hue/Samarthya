"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, Note } from "@/components/kit/Controls";

type Items = { items: { n: number; text: string }[]; scale: Record<string, string>; note: string; source: { title: string; url: string } };
type R = { code: string; flat_profile: boolean; note: string; types: { key: string; name: string; score: number; out_of: number; blurb: string; explore_terms: string[] }[]; source: { title: string; url: string } };

export default function Discover() {
  const [items, setItems] = useState<Items | null>(null);
  const [ans, setAns] = useState<Record<number, number>>({});
  const [out, setOut] = useState<R | null>(null);
  const { busy, error, run, setError } = useAction();
  useEffect(() => { call<Items>("GET", "/v1/tools/interests").then(setItems).catch((e) => setError((e as Error).message)); }, [setError]);
  if (!items) return <ErrorText>{error}</ErrorText>;
  const done = Object.keys(ans).length;
  async function go(e: React.FormEvent) {
    e.preventDefault();
    const r = await run(() => call<R>("POST", "/v1/tools/interests", { answers: items!.items.map((i) => ans[i.n]) }));
    if (r) setOut(r);
  }
  if (out) return (
    <div className="max-w-3xl" aria-live="polite">
      <h2 className="text-2xl font-semibold">Your top interest types: {out.code.split("").map((k) => out.types.find((t) => t.key === k)?.name).join(", ")}</h2>
      <p className="mt-2 text-slate">{out.note}</p>
      <ul className="mt-4 grid gap-3">{out.types.map((t) => (
        <li key={t.key} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-semibold">{t.name} <span className="text-sm font-normal text-slate">{t.score} of {t.out_of}</span></p><p className="text-sm">{t.blurb}</p>
          <p className="mt-2 text-sm">Explore: {t.explore_terms.map((x) => <Link key={x} className="mr-3 text-electric-blue underline" href={`/explore?q=${encodeURIComponent(x)}`}>{x}</Link>)}</p></li>))}</ul>
      <p className="mt-4 text-xs text-slate">Based on the Holland interest types used by the <a className="text-electric-blue underline" href={out.source.url} target="_blank" rel="noopener noreferrer">O*NET Interest Profiler<span className="sr-only"> (opens in a new tab)</span></a>. Your answers were scored on the spot and not saved.</p>
      <button className={`${btn} mt-4`} onClick={() => { setOut(null); setAns({}); }}>Start again</button>
    </div>);
  return (
    <form onSubmit={go} className="max-w-3xl">
      <Note>{items.note}</Note>
      <ol className="mt-4 grid gap-4">{items.items.map((i) => (
        <li key={i.n}><fieldset className="rounded-md border border-ink/10 bg-white p-4"><legend className="px-1 font-medium">{i.n + 1}. {i.text}</legend>
          <div className="mt-2 flex flex-wrap gap-4">{Object.entries(items.scale).map(([v, label]) => (
            <label key={v} className="flex items-center gap-2 text-sm"><input type="radio" name={`q${i.n}`} value={v} checked={ans[i.n] === Number(v)} onChange={() => setAns({ ...ans, [i.n]: Number(v) })} />{label}</label>))}</div></fieldset></li>))}</ol>
      <ErrorText>{error}</ErrorText>
      <p className="mt-4 text-sm text-slate" aria-live="polite">{done} of {items.items.length} answered</p>
      <button className={`${btn} mt-2`} disabled={busy || done < items.items.length}>See my interest types</button>
    </form>
  );
}

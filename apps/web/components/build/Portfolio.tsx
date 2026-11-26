"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";

type P = { slug: string; enabled: boolean; indexable: boolean; display_name: string; headline: string | null; bio: string | null; entry_ids: number[]; links: string[] };
type B = { introduction_draft: string | null; note: string; checklist: { item: string; done: boolean }[] };
const BLANK: P = { slug: "", enabled: false, indexable: false, display_name: "", headline: "", bio: "", entry_ids: [], links: [] };

export default function Portfolio() {
  const mine = useMine<P | null>("/v1/me/portfolio");
  const master = useMine<{ entries: { id: number; section: string; title: string }[] }>("/v1/me/master");
  const brand = useMine<B>("/v1/me/branding");
  const [p, setP] = useState<P>(BLANK);
  const [msg, setMsg] = useState("");
  const { busy, error, run } = useAction();
  useEffect(() => { if (mine.data) setP(mine.data); }, [mine.data]);
  async function save(e: React.FormEvent) { e.preventDefault(); const r = await run(() => call<P>("PUT", "/v1/me/portfolio", p)); if (r) setMsg("Saved."); }
  const set = (k: keyof P, v: unknown) => setP({ ...p, [k]: v });
  return (
    <div className="grid gap-8">
      {brand.data && (<section aria-labelledby="br" className="max-w-3xl"><h2 id="br" className="text-xl font-semibold">Personal branding checklist</h2><p className="text-sm text-slate">{brand.data.note}</p>
        {brand.data.introduction_draft && <blockquote className="mt-3 rounded-md border border-ink/10 bg-white p-3">{brand.data.introduction_draft}</blockquote>}
        <ul className="mt-3 grid gap-1">{brand.data.checklist.map((c) => <li key={c.item}><span aria-hidden>{c.done ? "✓" : "○"}</span> <span className="sr-only">{c.done ? "Done: " : "To do: "}</span>{c.item}</li>)}</ul></section>)}
      <form onSubmit={save} className="grid max-w-2xl gap-4"><h2 className="text-xl font-semibold">Your public page (optional)</h2>
        <Note>Nothing is public until you switch it on. Only the entries you tick appear. Samarthya does not verify these claims and says so on the page. Your email is never shown.</Note>
        <Labeled id="pn" label="Name to show"><input id="pn" className={inp} required value={p.display_name} onChange={(e) => set("display_name", e.target.value)} /></Labeled>
        <Labeled id="ps" label="Web address" help="Lowercase letters, numbers and hyphens, at least 3 characters."><div className="flex items-center gap-2"><span className="text-slate">/p/</span><input id="ps" className={inp} required pattern="[a-z0-9][a-z0-9-]{2,40}" value={p.slug} onChange={(e) => set("slug", e.target.value.toLowerCase())} /></div></Labeled>
        <Labeled id="ph" label="Headline"><input id="ph" className={inp} value={p.headline ?? ""} onChange={(e) => set("headline", e.target.value)} /></Labeled>
        <Labeled id="pb" label="About you"><textarea id="pb" rows={4} className={inp} value={p.bio ?? ""} onChange={(e) => set("bio", e.target.value)} /></Labeled>
        <fieldset><legend className="font-medium">Entries to show</legend><ul className="mt-2 grid gap-1">{(master.data?.entries ?? []).map((e) => <li key={e.id}><label className="flex items-center gap-2"><input type="checkbox" className="accent-electric-blue" checked={p.entry_ids.includes(e.id)} onChange={(ev) => set("entry_ids", ev.target.checked ? [...p.entry_ids, e.id] : p.entry_ids.filter((x) => x !== e.id))} />{e.title} <span className="text-sm text-slate">({e.section})</span></label></li>)}</ul></fieldset>
        <label className="flex items-center gap-2"><input type="checkbox" className="h-5 w-5 accent-electric-blue" checked={p.enabled} onChange={(e) => set("enabled", e.target.checked)} />Make this page public</label>
        <label className="flex items-center gap-2"><input type="checkbox" className="h-5 w-5 accent-electric-blue" checked={p.indexable} onChange={(e) => set("indexable", e.target.checked)} />Let search engines list it</label>
        <ErrorText>{error}</ErrorText>
        <div className="flex flex-wrap items-center gap-3"><button className={btn} disabled={busy}>Save</button>{p.enabled && p.slug && <Link className="text-electric-blue underline" href={`/p/${p.slug}`}>View public page</Link>}<span role="status" className="text-sm text-slate">{msg}</span></div></form>
    </div>
  );
}

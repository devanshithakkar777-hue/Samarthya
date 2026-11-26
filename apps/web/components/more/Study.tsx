"use client";

import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { danger, ErrorText, inp, Labeled, Note, small } from "@/components/kit/Controls";

type Lib = { results: { slug: string; title: string; access_url: string }[] };
type Note_ = { id: number; kind: string; quote: string | null; body: string; created_on: string };
type Notes = { item: { title: string; access_url: string }; notes: Note_[]; hint: string };

/** Student's own highlights and notes for one library item. The book is never copied: the student types what matters to them. */
export function LibraryNotes() {
  const lib = useMine<Lib>("/v1/library");
  const [slug, setSlug] = useState("");
  const notes = useMine<Notes>(slug ? `/v1/me/library-notes/${slug}` : null);
  const [kind, setKind] = useState("note"); const [quote, setQuote] = useState(""); const [body, setBody] = useState("");
  const { busy, error, run } = useAction();
  useEffect(() => { if (!slug && lib.data?.results[0]) setSlug(lib.data.results[0].slug); }, [lib.data, slug]);
  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (await run(() => call("POST", `/v1/me/library-notes/${slug}`, { kind, quote: quote || null, body }))) { setQuote(""); setBody(""); void notes.reload(); }
  }
  if (lib.data && !lib.data.results.length) return <Note>No library items are published yet, so there is nothing to attach notes to. Reviewers are checking the first ones.</Note>;
  return (
    <div className="max-w-3xl">
      <Labeled id="item" label="Library item"><select id="item" className={inp} value={slug} onChange={(e) => setSlug(e.target.value)}>
        {lib.data?.results.map((r) => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></Labeled>
      {notes.data && <><Note>{notes.data.hint}</Note>
        <p className="mt-2"><a className="text-electric-blue underline" href={notes.data.item.access_url} target="_blank" rel="noopener noreferrer">Open “{notes.data.item.title}” on its own site</a></p>
        <form onSubmit={add} className="mt-4 grid gap-3">
          <Labeled id="kind" label="Type"><select id="kind" className={inp} value={kind} onChange={(e) => setKind(e.target.value)}><option value="note">Note</option><option value="highlight">Highlight (a short quote)</option></select></Labeled>
          <Labeled id="quote" label="Short passage (optional, up to 300 characters)"><input id="quote" className={inp} maxLength={300} value={quote} onChange={(e) => setQuote(e.target.value)} /></Labeled>
          <Labeled id="body" label="Your note"><textarea id="body" className={inp} rows={3} maxLength={2000} value={body} onChange={(e) => setBody(e.target.value)} /></Labeled>
          <ErrorText>{error}</ErrorText>
          <div><button className={btn} disabled={busy || !(quote || body.trim())}>Save</button></div>
        </form>
        <ul className="mt-6 grid gap-3">{notes.data.notes.map((n) => (
          <li key={n.id} className="rounded-md border border-ink/10 bg-white p-3">
            <p className="text-xs uppercase text-slate">{n.kind} · {n.created_on}</p>
            {n.quote && <blockquote className="mt-1 border-l-4 border-electric-blue pl-3">{n.quote}</blockquote>}
            {n.body && <p className="mt-1 whitespace-pre-wrap">{n.body}</p>}
            <button className={`${danger} mt-2`} onClick={async () => { await run(() => call("DELETE", `/v1/me/library-notes/note/${n.id}`)); void notes.reload(); }}>Delete</button>
          </li>))}</ul></>}
    </div>
  );
}

type Node = { id: string; label: string; x: number; y: number }; type Edge = { from: string; to: string; label: string };
type MapRow = { id: number; title: string; boxes: number };

/** Simple concept map: add boxes, link them, move them by number. Saved privately. Keyboard friendly; no drag needed. */
export function ConceptMaps() {
  const list = useMine<{ maps: MapRow[] }>("/v1/me/concept-maps");
  const [id, setId] = useState<number | null>(null);
  const [title, setTitle] = useState("My concept map"); const [nodes, setNodes] = useState<Node[]>([]); const [edges, setEdges] = useState<Edge[]>([]);
  const [label, setLabel] = useState(""); const [a, setA] = useState(""); const [b, setB] = useState(""); const [rel, setRel] = useState("");
  const { busy, error, run } = useAction();
  async function open(mid: number) { const r = await call<{ title: string; nodes: Node[]; edges: Edge[] }>("GET", `/v1/me/concept-maps/${mid}`); setId(mid); setTitle(r.title); setNodes(r.nodes); setEdges(r.edges); }
  function addNode() { if (!label.trim()) return; const n = nodes.length; setNodes([...nodes, { id: String(Date.now() % 1e9), label: label.trim(), x: 40 + (n % 4) * 170, y: 30 + Math.floor(n / 4) * 90 }]); setLabel(""); }
  function link() { if (a && b && a !== b) { setEdges([...edges, { from: a, to: b, label: rel }]); setRel(""); } }
  async function save() {
    const r = await run(() => (id ? call<{ id: number }>("PUT", `/v1/me/concept-maps/${id}`, { title, nodes, edges }) : call<{ id: number }>("POST", "/v1/me/concept-maps", { title, nodes, edges })));
    if (r) { setId(r.id); void list.reload(); }
  }
  const by = Object.fromEntries(nodes.map((n) => [n.id, n]));
  return (
    <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
      <aside><h2 className="font-semibold">Your maps</h2>
        <ul className="mt-2 grid gap-1">{list.data?.maps.map((m) => <li key={m.id}><button className="text-electric-blue underline" onClick={() => open(m.id)}>{m.title} ({m.boxes})</button></li>)}</ul>
        <button className={`${small} mt-3`} onClick={() => { setId(null); setTitle("My concept map"); setNodes([]); setEdges([]); }}>New map</button></aside>
      <div>
        <Labeled id="mt" label="Title"><input id="mt" className={inp} value={title} onChange={(e) => setTitle(e.target.value)} maxLength={160} /></Labeled>
        <div className="mt-3 flex gap-2"><input aria-label="New box text" className={inp} placeholder="Add an idea" value={label} maxLength={80} onChange={(e) => setLabel(e.target.value)} onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addNode())} /><button className={small} onClick={addNode}>Add box</button></div>
        <div className="mt-3 grid gap-2 sm:grid-cols-4">
          <select aria-label="From box" className={inp} value={a} onChange={(e) => setA(e.target.value)}><option value="">From…</option>{nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}</select>
          <select aria-label="To box" className={inp} value={b} onChange={(e) => setB(e.target.value)}><option value="">To…</option>{nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}</select>
          <input aria-label="Link label" className={inp} placeholder="how are they linked?" value={rel} maxLength={60} onChange={(e) => setRel(e.target.value)} /><button className={small} onClick={link}>Link</button></div>
        <svg role="img" aria-label={`Concept map ${title}: ${nodes.length} boxes, ${edges.length} links`} viewBox="0 0 720 420" className="mt-4 w-full rounded-md border border-ink/10 bg-white">
          {edges.map((e, i) => { const f = by[e.from], t = by[e.to]; if (!f || !t) return null;
            return <g key={i}><line x1={f.x + 70} y1={f.y + 20} x2={t.x + 70} y2={t.y + 20} stroke="currentColor" strokeWidth="1.5" /><text x={(f.x + t.x) / 2 + 70} y={(f.y + t.y) / 2 + 16} fontSize="11" textAnchor="middle">{e.label}</text></g>; })}
          {nodes.map((n) => <g key={n.id}><rect x={n.x} y={n.y} width="140" height="40" rx="8" fill="white" stroke="currentColor" /><text x={n.x + 70} y={n.y + 25} fontSize="12" textAnchor="middle">{n.label.slice(0, 20)}</text></g>)}
        </svg>
        <p className="mt-2 text-sm text-slate">Boxes: {nodes.map((n) => n.label).join(", ") || "none yet"}. Links: {edges.map((e) => `${by[e.from]?.label} → ${by[e.to]?.label}${e.label ? ` (${e.label})` : ""}`).join("; ") || "none yet"}.</p>
        <ErrorText>{error}</ErrorText>
        <div className="mt-3 flex gap-2"><button className={btn} disabled={busy || !nodes.length} onClick={save}>Save map</button>
          {id && <button className={danger} onClick={async () => { await run(() => call("DELETE", `/v1/me/concept-maps/${id}`)); setId(null); setNodes([]); setEdges([]); void list.reload(); }}>Delete map</button>}</div>
      </div>
    </div>
  );
}

type Ans = { mode: string; answer: string; citations: { title?: string; path?: string }[]; own_notes: { title: string; text: string }[]; note: string; crisis_resources?: { name: string; phone: string }[] };

export function StudyAssistant() {
  const lib = useMine<Lib>("/v1/library");
  const [q, setQ] = useState(""); const [slug, setSlug] = useState(""); const [out, setOut] = useState<Ans | null>(null);
  const { busy, error, run } = useAction();
  async function go(e: React.FormEvent) { e.preventDefault(); const r = await run(() => call<Ans>("POST", "/v1/me/study-assistant", { question: q, library_slug: slug || null })); if (r) setOut(r); }
  return (
    <div className="max-w-3xl">
      <Note>Ask about a topic. Answers come from Samarthya's sourced pages and, if you pick a library item, from your own notes on it. The assistant cannot read the books themselves, and it will say when it has no sourced answer.</Note>
      <form onSubmit={go} className="mt-4 grid gap-3">
        <Labeled id="sq" label="Your question"><textarea id="sq" rows={3} className={inp} value={q} maxLength={1500} onChange={(e) => setQ(e.target.value)} required /></Labeled>
        <Labeled id="sl" label="Use my notes from (optional)"><select id="sl" className={inp} value={slug} onChange={(e) => setSlug(e.target.value)}><option value="">None</option>{lib.data?.results.map((r) => <option key={r.slug} value={r.slug}>{r.title}</option>)}</select></Labeled>
        <ErrorText>{error}</ErrorText><div><button className={btn} disabled={busy || q.trim().length < 2}>Ask</button></div>
      </form>
      {out && <div className="mt-6" aria-live="polite"><p className="whitespace-pre-wrap text-lg">{out.answer}</p>
        {out.crisis_resources && <ul className="mt-3">{out.crisis_resources.map((r) => <li key={r.name}>{r.name}: <strong>{r.phone}</strong></li>)}</ul>}
        {out.own_notes.length > 0 && <><h3 className="mt-4 font-semibold">From your notes</h3><ul>{out.own_notes.map((n, i) => <li key={i}>{n.text}</li>)}</ul></>}
        {out.citations.length > 0 && <p className="mt-3 text-sm">Sources: {out.citations.map((c, i) => <span key={i}>{c.path ? <a className="text-electric-blue underline" href={c.path}>{c.title ?? c.path}</a> : c.title}{i < out.citations.length - 1 ? ", " : ""}</span>)}</p>}
        <p className="mt-3 text-sm text-slate">{out.note}</p></div>}
    </div>
  );
}

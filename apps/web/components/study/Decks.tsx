"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import Crud from "@/components/kit/Crud";
import { danger, ErrorText, inp, Note, small } from "@/components/kit/Controls";

type Deck = { id: number; title: string; subject: string | null; cards: number; due: number };
type Card = { id: number; front: string; back: string };

export default function Decks() {
  const { data, reload, error } = useMine<Deck[]>("/v1/me/decks");
  const [title, setTitle] = useState("");
  const [active, setActive] = useState<Deck | null>(null);
  const [mode, setMode] = useState<"cards" | "review">("cards");
  const { busy, error: err, run } = useAction();
  if (active) return <DeckView deck={active} mode={mode} setMode={setMode} back={() => { setActive(null); void reload(); }} />;
  return (
    <div>
      <ErrorText>{error}</ErrorText>
      <form className="mb-5 flex max-w-xl gap-3" onSubmit={async (e) => { e.preventDefault(); if (await run(() => call("POST", "/v1/me/decks", { title }))) { setTitle(""); await reload(); } }}>
        <label htmlFor="deck" className="sr-only">New deck title</label>
        <input id="deck" className={inp} placeholder="New deck, for example Data structures" value={title} onChange={(e) => setTitle(e.target.value)} required />
        <button className={btn} disabled={busy}>Create</button>
      </form>
      <ErrorText>{err}</ErrorText>
      <ul className="grid gap-3 md:grid-cols-2">
        {(data ?? []).map((d) => (
          <li key={d.id} className="rounded-[var(--radius-lg)] border border-ink/10 bg-white p-4">
            <h3 className="font-semibold">{d.title}</h3><p className="text-sm text-slate">{d.cards} cards, {d.due} due today</p>
            <div className="mt-3 flex gap-2"><button className={small} onClick={() => { setMode("review"); setActive(d); }} disabled={d.due === 0}>Review due cards</button>
              <button className={small} onClick={() => { setMode("cards"); setActive(d); }}>Edit cards</button>
              <button className={danger} onClick={async () => { if (window.confirm("Delete this deck and its cards?")) { await call("DELETE", `/v1/me/decks/${d.id}`); await reload(); } }}>Delete</button></div>
          </li>))}
      </ul>
      {(data ?? []).length === 0 && <p className="text-slate">No decks yet.</p>}
    </div>
  );
}

function DeckView({ deck, mode, setMode, back }: { deck: Deck; mode: "cards" | "review"; setMode: (m: "cards" | "review") => void; back: () => void }) {
  return (
    <div>
      <button className={small} onClick={back}>Back to decks</button>
      <h3 className="my-4 text-xl font-semibold">{deck.title}</h3>
      {mode === "review" ? <Review deck={deck} done={() => setMode("cards")} /> : (
        <Crud path={`/v1/me/decks/${deck.id}/cards`} noun="card" empty="No cards yet."
          fields={[{ name: "front", label: "Front (question)", type: "textarea", required: true, rows: 3 }, { name: "back", label: "Back (answer)", type: "textarea", required: true, rows: 3 }]}
          render={(r) => (<><p className="font-medium">{String(r.front)}</p><p className="mt-1 text-sm text-slate">{String(r.back)}</p></>)} />
      )}
    </div>
  );
}

function Review({ deck, done }: { deck: Deck; done: () => void }) {
  const { data, reload } = useMine<Card[]>(`/v1/me/decks/${deck.id}/due`);
  const [shown, setShown] = useState(false);
  const [err, setErr] = useState("");
  const card = data?.[0];
  if (!data) return <p role="status">Loading…</p>;
  if (!card) return (<div><p className="text-lg">All done for today. Cards come back when they are due.</p><button className={`${btn} mt-4`} onClick={done}>Back to cards</button></div>);
  async function rate(rating: number) {
    try { await call("POST", `/v1/me/cards/${card!.id}/review`, { rating }); setShown(false); await reload(); } catch (e) { setErr((e as Error).message); }
  }
  return (
    <div className="max-w-xl rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
      <p className="text-sm text-slate">{data.length} due</p>
      <p className="mt-2 text-xl">{card.front}</p>
      {shown ? (<>
        <p className="mt-4 border-t border-ink/10 pt-4 text-lg">{card.back}</p>
        <p className="mt-4 text-sm text-slate">How well did you know it?</p>
        <div className="mt-2 flex flex-wrap gap-2">{([[1, "Not at all"], [3, "With effort"], [4, "Good"], [5, "Easily"]] as const).map(([n, l]) => <button key={n} className={small} onClick={() => rate(n)}>{l}</button>)}</div>
      </>) : <button className={`${btn} mt-4`} onClick={() => setShown(true)}>Show answer</button>}
      <ErrorText>{err}</ErrorText>
    </div>
  );
}

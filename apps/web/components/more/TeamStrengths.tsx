"use client";

import { useState } from "react";
import { inp } from "@/components/kit/Controls";
import { btn } from "@/components/ui";

const STRENGTHS = ["Planning and organising", "Creative ideas", "Research and checking facts", "Writing and editing", "Speaking and presenting", "Design and visuals", "Technical building", "Numbers and analysis", "Keeping everyone together", "Finishing and follow-through", "Asking good questions", "Staying calm under pressure"];
type P = { name: string; picks: string[] };

/** Runs entirely in your browser. Nothing you type here is sent or saved. */
export default function TeamStrengths() {
  const [people, setPeople] = useState<P[]>([{ name: "Me", picks: [] }]);
  const covered = new Set(people.flatMap((p) => p.picks));
  const gaps = STRENGTHS.filter((s) => !covered.has(s));
  const count = (s: string) => people.filter((p) => p.picks.includes(s)).length;
  return (
    <div className="grid max-w-3xl gap-6">
      <p className="rounded-md bg-ice-blue/40 p-3 text-sm">Nothing here is saved or sent. Pick what each person is genuinely good at, up to four each. Use the gaps to decide what to learn together or who to invite, not to judge anyone.</p>
      {people.map((p, i) => (
        <fieldset key={i} className="rounded-md border border-ink/10 bg-white p-4">
          <legend className="px-1 font-medium"><label className="sr-only" htmlFor={`n${i}`}>Name of person {i + 1}</label><input id={`n${i}`} className={inp} value={p.name} onChange={(e) => setPeople(people.map((x, j) => j === i ? { ...x, name: e.target.value.slice(0, 30) } : x))} /></legend>
          <div className="mt-2 grid gap-1 sm:grid-cols-2">{STRENGTHS.map((s) => <label key={s} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={p.picks.includes(s)} disabled={!p.picks.includes(s) && p.picks.length >= 4}
            onChange={(e) => setPeople(people.map((x, j) => j === i ? { ...x, picks: e.target.checked ? [...x.picks, s] : x.picks.filter((y) => y !== s) } : x))} />{s}</label>)}</div>
        </fieldset>))}
      <div className="flex gap-3"><button type="button" className={btn} disabled={people.length >= 8} onClick={() => setPeople([...people, { name: `Person ${people.length + 1}`, picks: [] }])}>Add a person</button>
        {people.length > 1 && <button type="button" className="rounded-md border border-ink/20 px-4 py-2" onClick={() => setPeople(people.slice(0, -1))}>Remove last</button>}</div>
      <section aria-live="polite" aria-labelledby="ts-h"><h2 id="ts-h" className="text-xl font-semibold">Team map</h2>
        <ul className="mt-2 grid gap-1 sm:grid-cols-2">{STRENGTHS.map((s) => <li key={s} className="rounded border border-ink/10 bg-white px-3 py-1 text-sm">{s}: {count(s) === 0 ? "nobody yet" : `${count(s)} ${count(s) === 1 ? "person" : "people"}`}</li>)}</ul>
        <p className="mt-3 text-sm">{gaps.length === 0 ? "Every area is covered by at least one person." : `Not covered yet: ${gaps.join(", ")}.`}</p></section>
    </div>
  );
}

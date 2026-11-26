"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { btn } from "@/components/ui";
import { inp } from "@/components/kit/Controls";

const STEPS = [
  ["Voice and breath", "Breathe slowly, speak a little slower than feels natural, pause between ideas."],
  ["Body and presence", "Stand or sit steady, look at people when you can, and use eye-contact alternatives if that is uncomfortable. Your accent is not a flaw."],
  ["Structure", "Open with your main point, give two or three supports, and close by repeating the point."],
  ["Stories", "One short real example beats three general claims: situation, what you did, what happened."],
  ["Under pressure", "Take a breath, repeat the question in your own words, and answer the part you know first."],
  ["Conversations and groups", "Listen fully, build on what others said, disagree with the idea and not the person."],
];
const SIMS: Record<string, { label: string; seconds: number; prompts: string[] }> = {
  extempore: { label: "Extempore", seconds: 60, prompts: ["A tool you could not live without", "Something small that changed your week", "A rule you would change in your college", "What makes a good teammate", "A place everyone should visit once"] },
  intro: { label: "Introduce yourself", seconds: 45, prompts: ["Introduce yourself to a recruiter at a career fair", "Introduce yourself to a new class", "Introduce yourself to a mentor you are meeting for the first time"] },
  gd: { label: "Group discussion opener", seconds: 60, prompts: ["Should students be allowed to use AI tools in exams?", "Is working from home better for freshers?", "Do campus placements measure ability fairly?"] },
  hard: { label: "Difficult conversation", seconds: 75, prompts: ["Tell a teammate calmly that they missed their part", "Ask a professor for an extension honestly", "Say no to extra work when you are already overloaded"] },
};
const CHECK = ["I started with my main point", "I gave one real example", "I paused instead of filling gaps", "I finished on time", "I spoke kindly about others"];

/** Nothing is recorded or sent. The timer is a guide, not a test, and nothing here rates accent, pace or confidence. */
export default function Elocution() {
  const [k, setK] = useState("extempore");
  const [prompt, setPrompt] = useState("");
  const [left, setLeft] = useState<number | null>(null);
  const [done, setDone] = useState<Record<string, boolean>>({});
  const t = useRef<ReturnType<typeof setInterval> | null>(null);
  const sim = SIMS[k];
  useEffect(() => () => { if (t.current) clearInterval(t.current); }, []);
  function start() {
    const p = sim.prompts[Math.floor(Math.random() * sim.prompts.length)];
    setPrompt(p); setDone({}); setLeft(sim.seconds);
    if (t.current) clearInterval(t.current);
    t.current = setInterval(() => setLeft((s) => { if (s === null || s <= 1) { if (t.current) clearInterval(t.current); return 0; } return s - 1; }), 1000);
  }
  return (
    <div className="grid max-w-3xl gap-8">
      <section aria-labelledby="six"><h2 id="six" className="mb-3 text-2xl font-semibold">Six steps</h2>
        <ol className="grid gap-2">{STEPS.map(([a, b], i) => <li key={a} className="rounded-md border border-ink/10 bg-white p-3"><p className="font-medium">{i + 1}. {a}</p><p className="text-sm">{b}</p></li>)}</ol>
        <p className="mt-2 text-sm"><Link className="text-electric-blue underline" href="/academy?pillar=elocution">Lessons for each step</Link> · <Link className="text-electric-blue underline" href="/learn/speaking">Voice and pronunciation practice</Link></p></section>
      <section aria-labelledby="sim"><h2 id="sim" className="mb-3 text-2xl font-semibold">Practice simulators</h2>
        <p className="mb-3 rounded-md bg-ice-blue/40 p-3 text-sm">Nothing is recorded or saved. The timer is only a guide. Speak out loud, to a mirror or a friend, then tick what you did.</p>
        <label htmlFor="sk" className="font-medium">Choose one</label>
        <select id="sk" className={inp} value={k} onChange={(e) => { setK(e.target.value); setPrompt(""); setLeft(null); }}>{Object.entries(SIMS).map(([key, v]) => <option key={key} value={key}>{v.label}</option>)}</select>
        <div className="mt-3"><button className={btn} onClick={start}>{prompt ? "Another prompt" : "Give me a prompt"}</button></div>
        {prompt && <div className="mt-4" aria-live="polite"><p className="text-xl font-semibold">{prompt}</p><p className="text-slate">About {sim.seconds} seconds{left !== null ? ` · ${left}s left` : ""}</p>
          {left === 0 && <ul className="mt-3 grid gap-2">{CHECK.map((c) => <li key={c}><label className="flex items-center gap-2"><input type="checkbox" checked={!!done[c]} onChange={(e) => setDone({ ...done, [c]: e.target.checked })} />{c}</label></li>)}</ul>}</div>}</section>
    </div>
  );
}

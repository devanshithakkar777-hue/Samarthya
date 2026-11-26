"use client";

import { useEffect, useRef, useState } from "react";
import { btn } from "@/components/ui";
import { inp, Labeled, Note, Tabs } from "@/components/kit/Controls";

/* eslint-disable @typescript-eslint/no-explicit-any */
const FILLERS = ["um", "uh", "erm", "like", "basically", "actually", "you know", "i mean", "sort of", "kind of"];
const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}\s']/gu, " ").split(/\s+/).filter(Boolean);

function lcs(a: string[], b: string[]) {
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
  return dp[a.length][b.length];
}

export default function Speaking() {
  const [mode, setMode] = useState("read");
  const [lang, setLang] = useState("en-IN");
  const [target, setTarget] = useState("The quick brown fox jumps over the lazy dog near the river bank.");
  const [text, setText] = useState("");
  const [live, setLive] = useState(false);
  const [secs, setSecs] = useState(0);
  const [supported, setSupported] = useState(true);
  const rec = useRef<any>(null);
  const t0 = useRef(0);
  useEffect(() => { setSupported(!!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)); }, []);
  useEffect(() => { if (!live) return; const id = setInterval(() => setSecs(Math.round((Date.now() - t0.current) / 1000)), 500); return () => clearInterval(id); }, [live]);

  function start() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const r = new SR();
    r.lang = lang; r.continuous = true; r.interimResults = true;
    let final = "";
    r.onresult = (e: any) => { let interim = ""; for (let i = e.resultIndex; i < e.results.length; i++) { const t = e.results[i][0].transcript; if (e.results[i].isFinal) final += t + " "; else interim += t; } setText((final + interim).trim()); };
    r.onend = () => setLive(false);
    r.onerror = () => setLive(false);
    rec.current = r; setText(""); setSecs(0); t0.current = Date.now(); setLive(true); r.start();
  }
  const stop = () => { rec.current?.stop(); setLive(false); };
  const hear = () => { const u = new SpeechSynthesisUtterance(target); u.lang = lang; speechSynthesis.cancel(); speechSynthesis.speak(u); };

  const spoken = norm(text), want = norm(target);
  const match = want.length ? Math.round((100 * lcs(want, spoken)) / want.length) : 0;
  const missed = want.filter((w) => !spoken.includes(w));
  const lower = text.toLowerCase();
  const fills = FILLERS.map((f) => [f, (lower.match(new RegExp(`\\b${f}\\b`, "g")) ?? []).length] as const).filter(([, n]) => n > 0);
  const wpm = secs > 5 ? Math.round((spoken.length / secs) * 60) : null;

  return (
    <div className="max-w-3xl">
      <Note>Practise speaking out loud. Your browser turns your voice into text. In some browsers, such as Chrome, the audio is sent to the browser maker&apos;s speech service to do this, so use it only for practice, never for private details. We do not receive or save your voice or the text.</Note>
      {!supported && <p role="alert" className="mt-4 rounded bg-ink p-3 text-arctic-white">Your browser does not support speech recognition. Try Chrome or Edge on a computer or Android phone. You can still type your answer below to check fillers.</p>}
      <div className="mt-4"><Tabs label="Practice type" value={mode} onChange={setMode} tabs={[{ key: "read", label: "Read aloud (pronunciation)" }, { key: "talk", label: "Speak freely (confidence)" }]} /></div>
      <Labeled id="lang" label="Language"><select id="lang" className={inp} value={lang} onChange={(e) => setLang(e.target.value)}><option value="en-IN">English (India)</option><option value="en-GB">English (UK)</option><option value="en-US">English (US)</option><option value="hi-IN">Hindi</option><option value="mr-IN">Marathi</option><option value="ta-IN">Tamil</option><option value="te-IN">Telugu</option><option value="bn-IN">Bengali</option></select></Labeled>
      {mode === "read" && <Labeled id="target" label="Passage to read" help="Paste any short passage, such as a paragraph from your own report or a speech you want to practise."><textarea id="target" rows={3} className={inp} value={target} onChange={(e) => setTarget(e.target.value)} /></Labeled>}
      <div className="mt-4 flex flex-wrap gap-3">
        {mode === "read" && <button type="button" className={btn} onClick={hear}>Hear it</button>}
        {!live ? <button type="button" className={btn} onClick={start} disabled={!supported}>Start speaking</button> : <button type="button" className={btn} onClick={stop}>Stop</button>}
      </div>
      <Labeled id="said" label={live ? "Listening… " + secs + "s" : "What we heard (you can also type here)"}><textarea id="said" rows={4} className={inp} value={text} onChange={(e) => setText(e.target.value)} /></Labeled>
      <div className="mt-4 rounded-md border border-ink/10 bg-white p-4" aria-live="polite">
        {mode === "read" ? (<><p className="text-xl font-semibold">{text ? `${match}% of the words matched` : "Read the passage, then see how much was recognised."}</p>
          {text && missed.length > 0 && <p className="mt-1 text-sm">Words to practise: {Array.from(new Set(missed)).slice(0, 15).join(", ")}</p>}
          <p className="mt-2 text-xs text-slate">A mismatch can mean the word was unclear, or that the recogniser misheard an accent. Use it as a prompt to listen again, not as a score.</p></>) : (<>
          <p className="text-xl font-semibold">{wpm ? `About ${wpm} words per minute` : "Speak for at least 10 seconds to see your pace."}</p>
          <p className="mt-1 text-sm">{fills.length ? `Filler words: ${fills.map(([f, n]) => `${f} (${n})`).join(", ")}` : text ? "No common filler words found." : ""}</p>
          <p className="mt-2 text-xs text-slate">Comfortable speech is often around 120 to 160 words per minute, but pace depends on the setting. Pauses are fine. Try answering a question such as &ldquo;Tell me about a project you are proud of&rdquo;.</p></>)}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Note, small } from "@/components/kit/Controls";

type Fb = { strengths: string[]; improvements: string[]; scores: Record<string, number>; mode: string };
type Mock = { id: number; finished: boolean; next_question: { n: number; of: number; text: string } | null; turns: { question: string; answer: string; feedback: Fb }[]; ai: boolean; note: string };

/** Mock interviewer. Questions can be read aloud (browser speech) and answers dictated (browser speech recognition, optional).
 *  Audio is handled by the student's own browser; Samarthya receives only the text the student submits. */
export function MockInterviewer() {
  const [mock, setMock] = useState<Mock | null>(null); const [ans, setAns] = useState(""); const [count, setCount] = useState(4);
  const [listening, setListening] = useState(false); const [speak, setSpeak] = useState(false);
  const rec = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const { busy, error, run } = useAction();
  const canListen = typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);
  useEffect(() => { if (speak && mock?.next_question && "speechSynthesis" in window) { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(mock.next_question.text)); } }, [speak, mock?.next_question]);
  function dictate() {
    if (listening) { rec.current?.stop(); return; }
    const W = window as any; const R = W.SpeechRecognition || W.webkitSpeechRecognition; if (!R) return; // eslint-disable-line @typescript-eslint/no-explicit-any
    const r = new R(); r.lang = "en-IN"; r.interimResults = false; r.continuous = true;
    r.onresult = (e: any) => setAns((a) => (a + " " + Array.from(e.results).slice(e.resultIndex).map((x: any) => x[0].transcript).join(" ")).trim()); // eslint-disable-line @typescript-eslint/no-explicit-any
    r.onend = () => setListening(false); rec.current = r; r.start(); setListening(true);
  }
  async function start() { const r = await run(() => call<Mock>("POST", "/v1/me/mock-interview", { count })); if (r) { setMock(r); setAns(""); } }
  async function send(e: React.FormEvent) { e.preventDefault(); const r = await run(() => call<Mock>("POST", `/v1/me/mock-interview/${mock!.id}/answer`, { answer: ans })); if (r && "turns" in r) { setMock(r); setAns(""); } }
  if (!mock) return (
    <div className="max-w-2xl"><Note>Practise answering interview questions out loud or in writing. You get feedback on structure and coverage. It cannot tell if your experiences are true, and it does not predict results. Nothing is shared with anyone.</Note>
      <label className="mt-4 block font-medium" htmlFor="cnt">How many questions?</label>
      <select id="cnt" className={inp} value={count} onChange={(e) => setCount(Number(e.target.value))}>{[2, 4, 6, 8].map((n) => <option key={n}>{n}</option>)}</select>
      <ErrorText>{error}</ErrorText><button className={`${btn} mt-4`} disabled={busy} onClick={start}>Start practice interview</button></div>);
  const q = mock.next_question;
  return (
    <div className="max-w-3xl">
      {mock.turns.map((t, i) => (<article key={i} className="mb-5 rounded-md border border-ink/10 bg-white p-4">
        <h3 className="font-semibold">Q{i + 1}. {t.question}</h3><p className="mt-1 whitespace-pre-wrap text-slate">{t.answer}</p>
        {t.feedback.strengths.length > 0 && <><h4 className="mt-2 font-medium">What worked</h4><ul className="list-disc pl-5">{t.feedback.strengths.map((s, j) => <li key={j}>{s}</li>)}</ul></>}
        {t.feedback.improvements.length > 0 && <><h4 className="mt-2 font-medium">To improve</h4><ul className="list-disc pl-5">{t.feedback.improvements.map((s, j) => <li key={j}>{s}</li>)}</ul></>}
        <p className="mt-1 text-xs text-slate">{t.feedback.mode === "ai" ? "AI feedback" : "Rule-based feedback"}</p></article>))}
      {q ? (<form onSubmit={send} className="grid gap-3"><h2 className="text-xl font-semibold" aria-live="polite">Question {q.n} of {q.of}: {q.text}</h2>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={speak} onChange={(e) => setSpeak(e.target.checked)} /> Read questions aloud</label>
        <textarea aria-label="Your answer" rows={6} className={inp} value={ans} onChange={(e) => setAns(e.target.value)} maxLength={4000} required />
        <ErrorText>{error}</ErrorText>
        <div className="flex flex-wrap gap-2"><button className={btn} disabled={busy || !ans.trim()}>Submit answer</button>
          {canListen && <button type="button" className={small} onClick={dictate}>{listening ? "Stop dictating" : "Dictate with microphone"}</button>}</div>
        {canListen && <p className="text-sm text-slate">Dictation uses your browser's speech service, which may send audio to its provider. Typing keeps everything on this site.</p>}</form>)
        : (<div><h2 className="text-xl font-semibold">Practice finished</h2><button className={`${btn} mt-3`} onClick={() => setMock(null)}>Start another</button></div>)}
      <p className="mt-4 text-sm text-slate">{mock.note}</p>
    </div>
  );
}

"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { call } from "@/lib/client";
import { btn } from "./ui";

function Form() {
  const sp = useSearchParams();
  const [message, setMessage] = useState("");
  const [contact, setContact] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      await call("POST", "/v1/reports", { message, contact: contact || null, page_url: sp.get("page") });
      setDone(true);
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }
  if (done) return <p role="status" className="rounded-lg bg-white p-6 text-lg">Thank you. A reviewer will check this against the source and fix it if needed.</p>;
  const input = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-3";
  return (
    <form onSubmit={submit} className="grid max-w-xl gap-4">
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      <div><label htmlFor="m" className="font-semibold">What is wrong or out of date?</label>
        <textarea id="m" required minLength={10} maxLength={2000} rows={5} className={input} value={message} onChange={(e) => setMessage(e.target.value)} /></div>
      <div><label htmlFor="c" className="font-semibold">Your email (optional, only if you want a reply)</label>
        <input id="c" type="email" className={input} value={contact} onChange={(e) => setContact(e.target.value)} /></div>
      <button className={btn} disabled={busy}>{busy ? "Sending…" : "Send report"}</button>
    </form>
  );
}
export default function ReportForm() { return <Suspense><Form /></Suspense>; }

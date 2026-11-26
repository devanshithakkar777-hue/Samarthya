"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useStudent } from "@/lib/student";
import { small } from "./kit/Controls";

/** Keeps a short note about the page you are reading in your own notes. */
export default function SaveNote({ title }: { title: string }) {
  const { user } = useStudent();
  const [state, setState] = useState<"idle" | "open" | "saved">("idle");
  const [body, setBody] = useState("");
  const [err, setErr] = useState("");
  if (!user) return null;
  if (state === "saved") return <p className="mt-6" role="status">Saved to <a className="text-electric-blue underline" href="/study">your notes</a>.</p>;
  if (state === "idle") return <button className={`${small} mt-6`} onClick={() => setState("open")}>Take a note about this</button>;
  return (
    <form className="mt-6 grid max-w-xl gap-2" onSubmit={async (e) => { e.preventDefault(); try { await call("POST", "/v1/me/notes", { title, body, folder: "Reading" }); setState("saved"); } catch (x) { setErr((x as Error).message); } }}>
      <label htmlFor="note" className="font-medium">Your note</label>
      <textarea id="note" rows={4} className="rounded-md border border-slate/50 bg-white px-3 py-2" value={body} onChange={(e) => setBody(e.target.value)} />
      {err && <p role="alert" className="rounded bg-ink p-2 text-arctic-white">{err}</p>}
      <div><button className={small}>Save note</button></div>
    </form>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useStudent } from "@/lib/student";

export default function PrivacyActions() {
  const { ready, user, deleteAccount, clearLocal } = useStudent();
  const [msg, setMsg] = useState("");
  const [confirm, setConfirm] = useState(false);
  if (!ready) return null;

  async function download() {
    setMsg("");
    try {
      const data = await call("GET", "/v1/me/export");
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const a = document.createElement("a"); a.href = url; a.download = "samarthya-my-data.json"; a.click(); URL.revokeObjectURL(url);
    } catch (e) { setMsg((e as Error).message); }
  }
  async function remove() {
    try { await deleteAccount(); setMsg("Your account and all its data have been deleted."); setConfirm(false); }
    catch (e) { setMsg((e as Error).message); }
  }

  return (
    <div id="export" className="grid gap-4 rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
      <h2 className="text-xl font-semibold">Your controls</h2>
      {msg && <p role="status">{msg}</p>}
      {user ? (
        <>
          <p>Signed in as <strong>{user.email}</strong>.</p>
          <div className="flex flex-wrap gap-3">
            <button onClick={download} className="rounded-md bg-electric-blue px-5 py-3 text-arctic-white">Download my data</button>
            {!confirm ? (
              <button onClick={() => setConfirm(true)} className="rounded-md border border-ink px-5 py-3">Delete my account</button>
            ) : (
              <span className="flex items-center gap-3"><span>This cannot be undone.</span>
                <button onClick={remove} className="rounded-md bg-ink px-5 py-3 text-arctic-white">Yes, delete everything</button>
                <button onClick={() => setConfirm(false)} className="underline">Cancel</button></span>
            )}
          </div>
        </>
      ) : (
        <>
          <p>You are not signed in. Your answers are stored only in this browser.</p>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => { clearLocal(); setMsg("Cleared from this device."); }} className="rounded-md border border-ink px-5 py-3">Clear data on this device</button>
            <Link href="/signin" className="rounded-md bg-electric-blue px-5 py-3 text-arctic-white">Sign in to save</Link>
          </div>
        </>
      )}
    </div>
  );
}

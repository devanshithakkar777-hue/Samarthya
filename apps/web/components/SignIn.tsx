"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { call } from "@/lib/client";
import { useStudent } from "@/lib/student";
import { btn } from "./ui";

export default function SignIn() {
  const router = useRouter();
  const { signedIn } = useStudent();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [stage, setStage] = useState<"email" | "code">("email");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function request(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { await call("POST", "/v1/auth/otp/request", { email }); setStage("code"); }
    catch (x) { setErr((x as Error).message); }
    finally { setBusy(false); }
  }
  async function verify(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const res = await fetch("/api/auth/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, code }) });
      const data = await res.json();
      if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : "That code did not work.");
      await signedIn(data.user);
      router.push("/dashboard");
    } catch (x) { setErr((x as Error).message); setBusy(false); }
  }
  const input = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-3";
  return (
    <div className="max-w-md">
      {err && <p role="alert" className="mb-4 rounded bg-ink p-3 text-arctic-white">{err}</p>}
      {stage === "email" ? (
        <form onSubmit={request} className="grid gap-4">
          <div><label htmlFor="email" className="font-semibold">Your email</label>
            <input id="email" type="email" autoComplete="email" required className={input} value={email} onChange={(e) => setEmail(e.target.value)} /></div>
          <button className={btn} disabled={busy}>{busy ? "Sending…" : "Email me a code"}</button>
          <p className="text-sm text-slate">We use your email only to sign you in. There are no passwords and no marketing mail.</p>
        </form>
      ) : (
        <form onSubmit={verify} className="grid gap-4">
          <p role="status">We sent a 6-digit code to <strong>{email}</strong>. It expires in a few minutes.</p>
          <div><label htmlFor="code" className="font-semibold">6-digit code</label>
            <input id="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required className={input} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} /></div>
          <button className={btn} disabled={busy || code.length !== 6}>{busy ? "Checking…" : "Sign in"}</button>
          <button type="button" className="text-left text-electric-blue underline" onClick={() => { setStage("email"); setCode(""); setErr(""); }}>Use a different email</button>
        </form>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { call } from "@/lib/client";
import { useStudent } from "@/lib/student";
import { btn } from "@/components/ui";

export default function TrackButton({ slug }: { slug: string }) {
  const { user } = useStudent();
  const [state, setState] = useState<"idle" | "done">("idle");
  const [err, setErr] = useState("");
  if (!user) return <p className="text-sm text-slate"><Link className="text-electric-blue underline" href="/signin">Sign in</Link> to track this in your applications.</p>;
  if (state === "done") return <p role="status">Added. <Link className="text-electric-blue underline" href="/applications">See your applications</Link>.</p>;
  return (<div><button className={btn} onClick={async () => { try { await call("POST", `/v1/me/applications/from-opportunity/${slug}`); setState("done"); } catch (e) { setErr((e as Error).message); } }}>Track this application</button>
    {err && <p role="alert" className="mt-2 rounded bg-ink p-2 text-arctic-white">{err}</p>}</div>);
}

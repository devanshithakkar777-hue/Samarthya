"use client";

import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { ErrorText, small } from "@/components/kit/Controls";
import Gate from "./Gate";

type Rep = { id: number; kind: string; target_id: number; reason: string; content: string | null; status: string; created_at: string };
type Mentor = { id: number; display_name: string; headline: string; bio: string; kind: string; expertise: string[]; profile_url: string };

function Body() {
  const reports = useMine<Rep[]>("/v1/moderation/reports");
  const mentors = useMine<Mentor[]>("/v1/moderation/mentors/pending");
  const { error, run } = useAction();
  return (
    <div className="grid gap-10">
      <ErrorText>{error || reports.error || mentors.error}</ErrorText>
      <section aria-labelledby="mr"><h2 id="mr" className="mb-3 text-xl font-semibold">Reports ({reports.data?.length ?? 0})</h2>
        <p className="mb-3 text-sm text-slate">Three separate reports hide an item automatically until you decide. Restore it, remove it, or dismiss the report.</p>
        <ul className="grid gap-3">{(reports.data ?? []).map((r) => (
          <li key={r.id} className="rounded-md border border-ink/10 bg-white p-4"><p className="text-sm text-slate">{r.kind} #{r.target_id} · currently {r.status}</p><p className="mt-1 whitespace-pre-line">{r.content ?? "(content no longer exists)"}</p><p className="mt-1 text-sm"><strong>Reason given:</strong> {r.reason}</p>
            <div className="mt-2 flex gap-2">{(["restore", "remove", "dismiss"] as const).map((a) => <button key={a} className={small} onClick={async () => { if (await run(() => call("POST", `/v1/moderation/reports/${r.id}`, { action: a }))) await reports.reload(); }}>{a[0].toUpperCase() + a.slice(1)}</button>)}</div></li>))}</ul></section>
      <section aria-labelledby="mm"><h2 id="mm" className="mb-3 text-xl font-semibold">Mentors waiting for approval ({mentors.data?.length ?? 0})</h2>
        <p className="mb-3 text-sm text-slate">Open the public profile and confirm the person is who they say they are before you approve. You cannot approve your own profile.</p>
        <ul className="grid gap-3">{(mentors.data ?? []).map((m) => (
          <li key={m.id} className="rounded-md border border-ink/10 bg-white p-4"><h3 className="font-semibold">{m.display_name} <span className="text-sm font-normal text-slate">{m.kind}</span></h3><p>{m.headline}</p><p className="mt-1 text-sm">{m.bio}</p><p className="mt-1 text-sm">Expertise: {m.expertise.join(", ") || "-"}</p>
            <p className="text-sm"><a className="text-electric-blue underline" href={m.profile_url} target="_blank" rel="noopener noreferrer">Public profile<span className="sr-only"> (opens in a new tab)</span></a></p>
            <div className="mt-2 flex gap-2">{(["approve", "reject"] as const).map((d) => <button key={d} className={small} onClick={async () => { if (await run(() => call("POST", `/v1/moderation/mentors/${m.id}`, { decision: d }))) await mentors.reload(); }}>{d === "approve" ? "Approve" : "Reject"}</button>)}</div></li>))}</ul></section>
    </div>
  );
}
export default function Moderation() { return <Gate need={["reviewer", "admin"]}>{() => <Body />}</Gate>; }

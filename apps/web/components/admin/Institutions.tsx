"use client";

import { useState } from "react";
import { call } from "@/lib/client";
import { useAction } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note } from "@/components/kit/Controls";
import Gate from "./Gate";

function Body() {
  const [f, setF] = useState({ name: "", slug: "", kind: "college" });
  const [created, setCreated] = useState<{ id: number; slug: string; join_code: string } | null>(null);
  const [staff, setStaff] = useState({ id: "", email: "", role: "placement" });
  const [msg, setMsg] = useState("");
  const { busy, error, run } = useAction();
  return (
    <div className="grid max-w-2xl gap-8">
      <Note>Institutions get a join code. Only a hash of it is stored, so it is shown once. Staff can see totals only, and only for groups of 10 or more students who chose to share.</Note>
      <form className="grid gap-4" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call<{ id: number; slug: string; join_code: string }>("POST", "/v1/org-admin/institutions", f)); if (r) setCreated(r); }}>
        <h2 className="text-xl font-semibold">Add an institution</h2>
        <Labeled id="in" label="Name"><input id="in" className={inp} required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Labeled>
        <Labeled id="is" label="Web address name (slug)"><input id="is" className={inp} required pattern="[a-z0-9][a-z0-9-]{1,60}" value={f.slug} onChange={(e) => setF({ ...f, slug: e.target.value })} /></Labeled>
        <div><button className={btn} disabled={busy}>Create</button></div></form>
      {created && <div role="status" className="rounded-md border-2 border-ink bg-white p-4"><p>Institution id <strong>{created.id}</strong>. Join code (copy it now, it will not be shown again):</p><p className="mt-1 select-all font-mono text-2xl">{created.join_code}</p></div>}
      <form className="grid gap-4" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call("POST", `/v1/org-admin/institutions/${staff.id}/staff`, { email: staff.email, role: staff.role })); if (r) setMsg("Staff member added."); }}>
        <h2 className="text-xl font-semibold">Add institution staff</h2>
        <Labeled id="si" label="Institution id"><input id="si" inputMode="numeric" className={inp} required value={staff.id} onChange={(e) => setStaff({ ...staff, id: e.target.value })} /></Labeled>
        <Labeled id="se" label="Their account email (they must have signed in once)"><input id="se" type="email" className={inp} required value={staff.email} onChange={(e) => setStaff({ ...staff, email: e.target.value })} /></Labeled>
        <Labeled id="sr" label="Role"><select id="sr" className={inp} value={staff.role} onChange={(e) => setStaff({ ...staff, role: e.target.value })}><option>placement</option><option>faculty</option><option>admin</option></select></Labeled>
        <div className="flex items-center gap-3"><button className={btn} disabled={busy}>Add staff</button><span role="status" className="text-sm">{msg}</span></div></form>
      <ErrorText>{error}</ErrorText>
    </div>
  );
}
export default function Institutions() { return <Gate need={["admin"]}>{() => <Body />}</Gate>; }

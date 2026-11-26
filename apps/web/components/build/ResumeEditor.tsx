"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { call } from "@/lib/client";
import { useAction, useMine } from "@/lib/useMine";
import { btn } from "@/components/ui";
import { ErrorText, inp, Labeled, Note, small, Tabs } from "@/components/kit/Controls";

type Entry = { id: number; section: string; title: string; organisation: string | null; bullets: string[]; basis?: string };
type Sel = { entry_id: number; bullets: number[] | null };
type Resume = { id: number; name: string; target_kind: string; target_ref: string | null; job_description: string | null; headline: string | null; summary: string | null;
  contact: { name?: string; email?: string; phone?: string; location?: string; links?: string[] }; selection: Sel[]; section_order: string[] };
type Finding = { severity: string; area: string; message: string };
type Version = { id: number; note: string; created_at: string };
type Preview = { name: string; headline: string | null; summary: string | null; contact: Resume["contact"]; sections: { key: string; label: string; items: { id: number; title: string; organisation: string | null; dates: string; detail: string | null; bullets: string[] }[] }[] };

const TARGETS = ["general", "role", "sector", "internship", "research", "academic_cv", "scholarship"];
const BLANK: Omit<Resume, "id"> = { name: "", target_kind: "general", target_ref: null, job_description: null, headline: null, summary: null, contact: {}, selection: [], section_order: [] };

export default function ResumeEditor({ id }: { id: string }) {
  const isNew = id === "new";
  const router = useRouter();
  const master = useMine<{ entries: Entry[] }>("/v1/me/master");
  const saved = useMine<Resume>(isNew ? null : `/v1/me/resumes/${id}`);
  const [r, setR] = useState<Omit<Resume, "id">>(BLANK);
  const [tab, setTab] = useState("choose");
  const { busy, error, run } = useAction();
  const [msg, setMsg] = useState("");
  useEffect(() => { if (saved.data) { const { id: _i, ...rest } = saved.data; void _i; setR(rest); } }, [saved.data]);
  const entries = master.data?.entries ?? [];
  const sel = new Map(r.selection.map((s) => [s.entry_id, s]));

  function toggle(e: Entry) { const next = new Map(sel); if (next.has(e.id)) next.delete(e.id); else next.set(e.id, { entry_id: e.id, bullets: null }); setR({ ...r, selection: [...next.values()] }); }
  function toggleBullet(e: Entry, i: number) {
    const cur = sel.get(e.id); if (!cur) return;
    const all = e.bullets.map((_, k) => k); const have = cur.bullets ?? all;
    const nb = have.includes(i) ? have.filter((x) => x !== i) : [...have, i].sort((a, b) => a - b);
    setR({ ...r, selection: r.selection.map((s) => (s.entry_id === e.id ? { ...s, bullets: nb.length === all.length ? null : nb } : s)) });
  }
  async function save() {
    const body = { ...r, name: r.name || "My resume", job_description: r.job_description || null, headline: r.headline || null, summary: r.summary || null, target_ref: r.target_ref || null };
    const out = await run(() => isNew ? call<Resume>("POST", "/v1/me/resumes", body) : call<Resume>("PUT", `/v1/me/resumes/${id}`, body));
    if (out) { setMsg("Saved."); if (isNew) router.replace(`/build/resumes/${out.id}`); else await saved.reload(); }
  }
  async function suggest() {
    if (isNew) { setMsg("Save the resume first, then ask for suggestions."); return; }
    await save();
    const out = await run(() => call<{ selection: Sel[]; titles: string[]; note: string }>("POST", `/v1/me/resumes/${id}/suggest`));
    if (out) { setR({ ...r, selection: out.selection }); setMsg(`${out.note} Suggested: ${out.titles.join(", ") || "nothing yet"}. Press Save to keep it.`); }
  }
  const set = (k: keyof typeof r, v: unknown) => setR({ ...r, [k]: v });
  const grouped = entries.reduce<Record<string, Entry[]>>((a, e) => { (a[e.section] ??= []).push(e); return a; }, {});

  return (
    <div className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Labeled id="rn" label="Name this resume"><input id="rn" className={inp} value={r.name} onChange={(e) => set("name", e.target.value)} placeholder="For example Data analyst internships" /></Labeled>
        <Labeled id="rt" label="Aimed at"><select id="rt" className={inp} value={r.target_kind} onChange={(e) => set("target_kind", e.target.value)}>{TARGETS.map((t) => <option key={t}>{t}</option>)}</select></Labeled>
        <Labeled id="rr" label="Role or sector slug (optional)" help="From the address of a role or sector page. Used to look for matching words."><input id="rr" className={inp} value={r.target_ref ?? ""} onChange={(e) => set("target_ref", e.target.value)} /></Labeled>
        <Labeled id="rh" label="Headline"><input id="rh" className={inp} value={r.headline ?? ""} onChange={(e) => set("headline", e.target.value)} placeholder="What you do, in a few words" /></Labeled>
        <div className="md:col-span-2"><Labeled id="rs" label="Summary (2 to 3 lines, in your own words)"><textarea id="rs" rows={3} className={inp} value={r.summary ?? ""} onChange={(e) => set("summary", e.target.value)} /></Labeled></div>
        <div className="md:col-span-2"><Labeled id="rj" label="Job description to tailor for (paste it here, optional)" help="Used only to compare words and suggest what to include. Nothing is rewritten for you."><textarea id="rj" rows={4} className={inp} value={r.job_description ?? ""} onChange={(e) => set("job_description", e.target.value)} /></Labeled></div>
        {(["name", "email", "phone", "location"] as const).map((k) => <Labeled key={k} id={`c-${k}`} label={`Contact: ${k}`}><input id={`c-${k}`} className={inp} value={r.contact[k] ?? ""} onChange={(e) => set("contact", { ...r.contact, [k]: e.target.value })} /></Labeled>)}
        <div className="md:col-span-2"><Labeled id="cl" label="Links (one per line, https://)"><textarea id="cl" rows={2} className={inp} value={(r.contact.links ?? []).join("\n")} onChange={(e) => set("contact", { ...r.contact, links: e.target.value.split("\n").map((s) => s.trim()).filter(Boolean) })} /></Labeled></div>
      </div>
      <ErrorText>{error}</ErrorText>
      <div className="flex flex-wrap items-center gap-3"><button className={btn} onClick={save} disabled={busy}>{busy ? "Saving…" : "Save"}</button>
        {!isNew && <button className={small} onClick={suggest} disabled={busy}>Suggest what to include</button>}<span role="status" className="text-sm text-slate">{msg}</span></div>
      {!isNew && <Tabs label="Resume tools" value={tab} onChange={setTab} tabs={[{ key: "choose", label: "Choose entries" }, { key: "preview", label: "Preview" }, { key: "check", label: "Checks" }, { key: "versions", label: "Versions" }, { key: "export", label: "Download" }]} />}
      {(tab === "choose" || isNew) && (entries.length === 0 ? <Note>Your master profile is empty. <Link className="text-electric-blue underline" href="/build">Add entries first</Link>.</Note> : (
        <div className="grid gap-5">{Object.entries(grouped).map(([sec, es]) => (
          <fieldset key={sec}><legend className="font-semibold capitalize">{sec}</legend>
            <ul className="mt-2 grid gap-2">{es.map((e) => { const s = sel.get(e.id); const have = s?.bullets ?? e.bullets.map((_, k) => k); return (
              <li key={e.id} className="rounded-md border border-ink/10 bg-white p-3"><label className="flex items-start gap-3"><input type="checkbox" className="mt-1 h-5 w-5 accent-electric-blue" checked={!!s} onChange={() => toggle(e)} />
                <span><strong>{e.title}</strong>{e.organisation ? <span className="text-slate"> · {e.organisation}</span> : null}{e.basis ? <span className="ml-2 text-xs text-slate">({e.basis})</span> : null}</span></label>
                {s && e.bullets.length > 0 && <ul className="ml-8 mt-2 grid gap-1">{e.bullets.map((b, i) => <li key={i}><label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1 accent-electric-blue" checked={have.includes(i)} onChange={() => toggleBullet(e, i)} />{b}</label></li>)}</ul>}</li>); })}</ul></fieldset>))}</div>))}
      {!isNew && tab === "preview" && <PreviewPane id={id} />}
      {!isNew && tab === "check" && <><CheckPane id={id} /><CompanyCopy id={id} /></>}
      {!isNew && tab === "versions" && <Versions id={id} onRestore={saved.reload} />}
      {!isNew && tab === "export" && (<div className="grid gap-3"><Note>Download your resume as a file. The Word file is best if you want to edit it further or use Hindi or other Indian-language text; the PDF uses a standard font.</Note>
        <div className="flex flex-wrap gap-3"><a className={btn} href={`/api/proxy/v1/me/resumes/${id}/export.docx`}>Download Word (.docx)</a><a className={small} href={`/api/proxy/v1/me/resumes/${id}/export.pdf`}>Download PDF</a><Link className={small} href={`/build/defence?resume=${id}`}>Practise defending it</Link></div></div>)}
    </div>
  );
}

function PreviewPane({ id }: { id: string }) {
  const { data, error } = useMine<Preview>(`/v1/me/resumes/${id}/preview`);
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p role="status">Loading…</p>;
  return (
    <article className="max-w-3xl rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
      <h2 className="text-2xl font-semibold">{data.name}</h2>{data.headline && <p>{data.headline}</p>}
      <p className="text-sm text-slate">{[data.contact.email, data.contact.phone, data.contact.location, ...(data.contact.links ?? [])].filter(Boolean).join(" · ")}</p>
      {data.summary && <p className="mt-3">{data.summary}</p>}
      {data.sections.map((s) => <section key={s.key} className="mt-4"><h3 className="border-b border-ink/20 pb-1 font-semibold uppercase tracking-wide">{s.label}</h3>
        {s.items.map((it) => <div key={it.id} className="mt-2"><p className="font-medium">{it.title}{it.organisation ? `, ${it.organisation}` : ""}<span className="float-right text-sm font-normal text-slate">{it.dates}</span></p>{it.detail && <p className="text-sm text-slate">{it.detail}</p>}
          {it.bullets.length > 0 && <ul className="list-disc pl-5 text-sm">{it.bullets.map((b, i) => <li key={i}>{b}</li>)}</ul>}</div>)}</section>)}
    </article>
  );
}

function CompanyCopy({ id }: { id: string }) {
  const router = useRouter();
  const [slug, setSlug] = useState("");
  const { busy, error, run } = useAction();
  return (
    <form className="mt-4 flex max-w-xl flex-wrap items-end gap-2" onSubmit={async (e) => { e.preventDefault(); const r = await run(() => call<{ id: number }>("POST", `/v1/me/resumes/${id}/company-copy`, { company_slug: slug.trim() })); if (r) router.push(`/build/resumes/${r.id}`); }}>
      <div className="grow"><label htmlFor="cc" className="text-sm font-medium">Make a copy for one company (its page address, for example acme-ltd)</label><input id="cc" className="mt-1 w-full rounded-md border border-slate/50 px-3 py-2" value={slug} onChange={(e) => setSlug(e.target.value)} required /></div>
      <button className="rounded-md border border-ink/20 px-4 py-2" disabled={busy}>Copy for company</button><ErrorText>{error}</ErrorText></form>
  );
}

function CheckPane({ id }: { id: string }) {
  const { data, error } = useMine<{ findings: Finding[]; stats: Record<string, number>; alignment?: { matched: string[]; missing: string[]; basis?: string } | null; ats_note?: string }>(`/v1/me/resumes/${id}/check`);
  if (error) return <ErrorText>{error}</ErrorText>;
  if (!data) return <p role="status">Loading…</p>;
  return (
    <div className="max-w-3xl grid gap-4">
      <Note>These checks point at gaps. They are not a score and they cannot tell you how an employer&apos;s system will treat your resume. You decide what to change.</Note>
      <p className="text-sm text-slate">{Object.entries(data.stats).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" · ")}</p>
      {data.findings.length === 0 ? <p>No issues found.</p> : <ul className="grid gap-2">{data.findings.map((f, i) => <li key={i} className="rounded-md border border-ink/10 bg-white p-3"><span className="text-xs uppercase text-slate">{f.area} · {f.severity}</span><p>{f.message}</p></li>)}</ul>}
      {data.alignment && (data.alignment.matched.length > 0 || data.alignment.missing.length > 0) && <div><h3 className="font-semibold">Words from the {data.alignment.basis ?? "job description"}</h3><p className="text-sm">Already in your resume: {data.alignment.matched.join(", ") || "none"}.</p><p className="text-sm">Not in your resume: {data.alignment.missing.join(", ") || "none"}. Add one only if it is true for you.</p></div>}
      <GapPane id={id} />
      {data.ats_note && <p className="text-sm text-slate">{data.ats_note}</p>}
    </div>
  );
}

const STATE_LABEL: Record<string, string> = { demonstrated: "Demonstrated", have: "Have", claimed: "Claimed only", out_of_date: "Out of date", to_acquire: "To acquire" };
function GapPane({ id }: { id: string }) {
  const { data } = useMine<{ basis: string | null; items: { term: string; state: string; evidence: string[] }[]; summary: Record<string, number>; meaning?: Record<string, string>; note: string; learn?: { term: string; skill: string; name: string }[] }>(`/v1/me/resumes/${id}/gaps`);
  if (!data) return null;
  if (!data.basis) return <Note>{data.note}</Note>;
  return (
    <section aria-labelledby="gap-h">
      <h3 id="gap-h" className="text-lg font-semibold">Gap analysis against the {data.basis}</h3>
      <p className="mb-2 text-sm text-slate">{data.note}</p>
      <ul className="grid gap-2 sm:grid-cols-2">{Object.keys(STATE_LABEL).map((k) => { const list = data.items.filter((i) => i.state === k); return list.length ? (
        <li key={k} className="rounded-md border border-ink/10 bg-white p-3"><p className="font-medium">{STATE_LABEL[k]} ({list.length})</p><p className="text-sm text-slate">{data.meaning?.[k]}</p>
          <p className="mt-1 text-sm">{list.map((i) => i.term).join(", ")}</p></li>) : null; })}</ul>
      {(data.learn ?? []).length > 0 && <p className="mt-3 text-sm">Learn: {(data.learn ?? []).map((l, i) => <span key={l.skill}>{i > 0 && ", "}<Link className="text-electric-blue underline" href={`/skills/${l.skill}`}>{l.name}</Link></span>)}</p>}
    </section>
  );
}

function Versions({ id, onRestore }: { id: string; onRestore: () => Promise<void> }) {
  const { data, reload } = useMine<Version[]>(`/v1/me/resumes/${id}/versions`);
  const { error, run } = useAction();
  return (
    <div className="max-w-2xl"><ErrorText>{error}</ErrorText>
      <ul className="grid gap-2">{(data ?? []).map((v) => <li key={v.id} className="flex items-center justify-between rounded-md border border-ink/10 bg-white p-3"><span>{v.note} <span className="text-sm text-slate">{new Date(v.created_at).toLocaleString("en-IN")}</span></span>
        <button className={small} onClick={async () => { if (await run(() => call("POST", `/v1/me/resumes/${id}/restore/${v.id}`))) { await onRestore(); await reload(); } }}>Restore</button></li>)}</ul></div>
  );
}

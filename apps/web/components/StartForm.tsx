"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useStudent } from "@/lib/student";
import type { Qualification, SectorCard } from "@/lib/types";
import { btn } from "./ui";

function Form({ quals, sectors }: { quals: Qualification[]; sectors: SectorCard[] }) {
  const router = useRouter();
  const sp = useSearchParams();
  const { profile, ready, saveProfile } = useStudent();
  const [q, setQ] = useState(sp.get("q") ?? "");
  const [year, setYear] = useState("");
  const [grad, setGrad] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!ready) return;
    if (!sp.get("q") && profile.qualification) setQ(profile.qualification);
    if (profile.year_of_study) setYear(String(profile.year_of_study));
    if (profile.expected_graduation_year) setGrad(String(profile.expected_graduation_year));
    if (profile.interests.length) setInterests(profile.interests);
  }, [ready]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (slug: string) => setInterests((c) => (c.includes(slug) ? c.filter((x) => x !== slug) : [...c, slug]));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    if (!q) { setErr("Please choose your degree, or pick “Not sure yet” to see everything."); return; }
    if (q === "none" && interests.length === 0) { setErr("Pick at least one interest so we have something to show you."); return; }
    setBusy(true);
    try {
      await saveProfile({
        qualification: q === "none" ? null : q,
        year_of_study: year ? Number(year) : null,
        expected_graduation_year: grad ? Number(grad) : null,
        interests, skills: profile.skills,
      });
      router.push("/results");
    } catch {
      setErr("We could not save your answers. Please try again.");
      setBusy(false);
    }
  }

  const field = "mt-1 w-full rounded-md border border-slate/50 bg-white px-3 py-3";
  return (
    <form onSubmit={submit} className="grid max-w-2xl gap-8" noValidate>
      {err && <p role="alert" className="rounded bg-ink p-3 text-arctic-white">{err}</p>}
      <div>
        <label htmlFor="q" className="text-lg font-semibold">What are you studying?</label>
        <select id="q" className={field} value={q} onChange={(e) => setQ(e.target.value)} required>
          <option value="">Choose your degree</option>
          {quals.map((x) => (<option key={x.id} value={x.slug}>{x.degree}{x.specialization ? `, ${x.specialization}` : ""}</option>))}
          <option value="none">Not sure yet</option>
        </select>
        {!quals.length && <p className="mt-2 text-sm text-slate">Degrees are being added. You can still choose “Not sure yet” to browse everything.</p>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="y" className="font-semibold">Year of study (optional)</label>
          <select id="y" className={field} value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="">Prefer not to say</option>
            {[1, 2, 3, 4, 5, 6].map((n) => (<option key={n} value={n}>Year {n}</option>))}
          </select>
        </div>
        <div>
          <label htmlFor="g" className="font-semibold">Expected graduation year (optional)</label>
          <input id="g" inputMode="numeric" pattern="[0-9]{4}" maxLength={4} className={field} value={grad} onChange={(e) => setGrad(e.target.value.replace(/\D/g, ""))} placeholder="e.g. 2029" />
        </div>
      </div>
      <fieldset>
        <legend className="text-lg font-semibold">What interests you? (pick any)</legend>
        {sectors.length ? (
          <div className="mt-3 flex flex-wrap gap-3">
            {sectors.map((s) => (
              <label key={s.id} className={`cursor-pointer rounded-full border px-4 py-2 ${interests.includes(s.slug) ? "border-electric-blue bg-electric-blue text-arctic-white" : "border-slate/50 bg-white"}`}>
                <input type="checkbox" className="sr-only" checked={interests.includes(s.slug)} onChange={() => toggle(s.slug)} />
                {s.name}
              </label>
            ))}
          </div>
        ) : <p className="mt-2 text-slate">Sectors will appear here once published.</p>}
      </fieldset>
      <div><button className={btn} disabled={busy}>{busy ? "Saving…" : "Show my options"}</button></div>
    </form>
  );
}

export default function StartForm(props: { quals: Qualification[]; sectors: SectorCard[] }) {
  return (<Suspense><Form {...props} /></Suspense>);
}

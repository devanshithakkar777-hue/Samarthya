"use client";

import Link from "next/link";
import { useState } from "react";
import { inp } from "@/components/kit/Controls";
import { PageHead, Section } from "@/components/ui";

const GOALS: Record<string, { label: string; kind: string; note: string }> = {
  government: { label: "A government job (central, state, banking, railways, defence)", kind: "government_exam", note: "Read the official notification for age, attempts, education and dates. Each exam sets its own rules." },
  higher: { label: "A master's or other higher studies in India", kind: "entrance_exam", note: "Entrance exams differ by course and university. Check each university's official page." },
  abroad: { label: "Studying abroad", kind: "higher_education", note: "Check the university's official admission page for tests, funding and visa rules." },
  funding: { label: "A scholarship or financial support", kind: "scholarship", note: "Check eligibility, last dates and documents on the official scholarship page." },
};
export default function Page() {
  const [g, setG] = useState("government");
  const [y, setY] = useState("");
  const x = GOALS[g];
  return (<><PageHead title="Which exam or route fits me?" lead="Answer two questions and jump to the published, sourced listings. This page never decides for you, and it does not guess eligibility." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section><div className="grid max-w-2xl gap-4">
      <div><label htmlFor="g" className="font-medium">What are you aiming for?</label><select id="g" className={inp} value={g} onChange={(e) => setG(e.target.value)}>{Object.entries(GOALS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></div>
      <div><label htmlFor="y" className="font-medium">Your year of study</label><select id="y" className={inp} value={y} onChange={(e) => setY(e.target.value)}><option value="">Any</option>{[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>Year {n}</option>)}</select></div>
      <p className="rounded-md bg-ice-blue/40 p-3">{x.note}</p>
      <p><Link className="text-lg text-electric-blue underline" href={`/opportunities?kind=${x.kind}${y ? `&year=${y}` : ""}`}>See published {x.kind.replace(/_/g, " ")} listings</Link></p>
      <p className="text-sm text-slate">Rules, dates and attempt limits change. Always confirm on the official notice before you plan around any date.</p></div></Section></>);
}

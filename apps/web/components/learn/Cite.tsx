"use client";

import { useState } from "react";
import { btn } from "@/components/ui";
import { inp, Labeled, Note, Tabs } from "@/components/kit/Controls";

type Kind = "book" | "article" | "web";
type F = Record<string, string>;
const MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function people(raw: string) {
  return raw.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
    const [last, first = ""] = l.includes(",") ? l.split(/,(.+)/).map((x) => x.trim()) : [l.split(" ").slice(-1)[0], l.split(" ").slice(0, -1).join(" ")];
    return { last, first, initials: first.split(/[\s.]+/).filter(Boolean).map((p) => p[0].toUpperCase() + ".").join(" ") };
  });
}
function join(list: string[], last: string) { return list.length <= 1 ? list.join("") : list.slice(0, -1).join(", ") + (list.length > 2 ? "," : "") + ` ${last} ` + list[list.length - 1]; }
const dot = (s: string) => (/[.?!]$/.test(s) ? s : s + ".");

/** Returns segments; text between asterisks is italic. Accuracy rests on what the student types: always check the result against your institution's guide. */
export function format(style: string, kind: Kind, f: F): string {
  const a = people(f.authors ?? "");
  const yr = f.year || "n.d.";
  const url = f.doi ? (f.doi.startsWith("http") ? f.doi : `https://doi.org/${f.doi}`) : f.url;
  const pages = f.pages ? f.pages.replace(/-/g, "–") : "";
  if (style === "apa") {
    const au = join(a.map((p) => `${p.last}, ${p.initials}`.trim()), "&").replace(/,\s*&/, ", &");
    const lead = au ? dot(au) + " " : "";
    if (kind === "book") return `${lead}(${yr}). *${f.title}*${f.edition ? ` (${f.edition} ed.)` : ""}. ${f.publisher || ""}${url ? `. ${url}` : ""}`.replace(/\.\./g, ".").trim();
    if (kind === "article") return `${lead}(${yr}). ${dot(f.title)} *${f.container}${f.volume ? `, ${f.volume}` : ""}*${f.issue ? `(${f.issue})` : ""}${pages ? `, ${pages}` : ""}.${url ? ` ${url}` : ""}`;
    const d = f.day && f.month ? `${yr}, ${MON[Number(f.month) - 1] ?? ""} ${f.day}` : yr;
    return `${lead || (f.container ? "" : "")}(${d}). *${f.title}*. ${f.container ? dot(f.container) + " " : ""}${url ?? ""}`.trim();
  }
  if (style === "mla") {
    const names = a.map((p, i) => (i === 0 ? `${p.last}, ${p.first}` : `${p.first} ${p.last}`).trim());
    const au = a.length > 2 ? `${a[0].last}, ${a[0].first}, et al` : join(names, "and");
    const lead = au ? dot(au) + " " : "";
    if (kind === "book") return `${lead}*${f.title}*. ${f.edition ? `${f.edition} ed., ` : ""}${f.publisher ? f.publisher + ", " : ""}${yr}.`;
    if (kind === "article") return `${lead}“${dot(f.title)}” *${f.container}*, ${f.volume ? `vol. ${f.volume}, ` : ""}${f.issue ? `no. ${f.issue}, ` : ""}${yr}${pages ? `, pp. ${pages}` : ""}${url ? `, ${url}` : ""}.`;
    const d = f.day && f.month ? `${f.day} ${MON[Number(f.month) - 1]?.slice(0, 3)}. ${yr}` : yr;
    return `${lead}“${dot(f.title)}” *${f.container || ""}*${f.container ? ", " : ""}${d}${url ? `, ${url}` : ""}.`;
  }
  const au = join(a.map((p) => `${p.last}, ${p.initials}`.trim()), "and");
  const lead = au ? `${au} ` : "";
  if (kind === "book") return `${lead}(${yr}) *${f.title}*.${f.edition ? ` ${f.edition} edn.` : ""}${f.place ? ` ${f.place}:` : ""} ${f.publisher || ""}.`;
  if (kind === "article") return `${lead}(${yr}) ‘${f.title}’, *${f.container}*${f.volume ? `, ${f.volume}` : ""}${f.issue ? `(${f.issue})` : ""}${pages ? `, pp. ${pages}` : ""}.${url ? ` Available at: ${url}` : ""}`;
  return `${lead}(${yr}) *${f.title}*. Available at: ${url ?? ""} (Accessed: ${f.accessed || "date"}).`;
}

function Rendered({ text }: { text: string }) {
  return <>{text.split("*").map((s, i) => (i % 2 ? <i key={i}>{s}</i> : <span key={i}>{s}</span>))}</>;
}

export default function Cite() {
  const [style, setStyle] = useState("apa");
  const [kind, setKind] = useState<Kind>("book");
  const [f, setF] = useState<F>({});
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  const out = f.title ? format(style, kind, f) : "";
  const txt = (id: string, label: string, help?: string) => <Labeled id={id} label={label} help={help}><input id={id} className={inp} value={f[id] ?? ""} onChange={set(id)} /></Labeled>;
  return (
    <div className="max-w-3xl">
      <Note>Type the details from the source and get a reference in the style you choose. Always check the result against your college&apos;s own guide, because departments differ. Nothing leaves your browser.</Note>
      <div className="mt-4"><Tabs label="Style" value={style} onChange={setStyle} tabs={[{ key: "apa", label: "APA 7" }, { key: "mla", label: "MLA 9" }, { key: "harvard", label: "Harvard" }]} />
        <Tabs label="Source type" value={kind} onChange={(k) => setKind(k as Kind)} tabs={[{ key: "book", label: "Book" }, { key: "article", label: "Journal article" }, { key: "web", label: "Web page" }]} /></div>
      <div className="grid gap-3 md:grid-cols-2">
        <Labeled id="authors" label="Authors" help="One per line, as Last, First"><textarea id="authors" rows={3} className={inp} value={f.authors ?? ""} onChange={set("authors")} /></Labeled>
        {txt("year", "Year")}{txt("title", kind === "book" ? "Book title" : kind === "article" ? "Article title" : "Page title")}
        {kind !== "book" && txt("container", kind === "article" ? "Journal name" : "Website name")}
        {kind === "book" && <>{txt("publisher", "Publisher")}{txt("place", "Place of publication (Harvard)")}{txt("edition", "Edition (e.g. 2nd)")}</>}
        {kind === "article" && <>{txt("volume", "Volume")}{txt("issue", "Issue")}{txt("pages", "Pages (e.g. 12-30)")}{txt("doi", "DOI")}</>}
        {kind === "web" && <>{txt("url", "Web address")}{txt("day", "Day published")}{txt("month", "Month published (1-12)")}{txt("accessed", "Date you read it (Harvard)")}</>}
      </div>
      <div className="mt-6 rounded-md border border-ink/10 bg-white p-4" aria-live="polite"><p className="text-sm text-slate">Reference</p>
        <p className="mt-1 break-words">{out ? <Rendered text={out} /> : "Fill in the details to see it here."}</p></div>
      {out && <button className={`${btn} mt-3`} onClick={() => navigator.clipboard?.writeText(out.replace(/\*/g, ""))}>Copy as plain text</button>}
    </div>
  );
}

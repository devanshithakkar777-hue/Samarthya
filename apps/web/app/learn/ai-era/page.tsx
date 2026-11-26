import type { Metadata } from "next";
import Link from "next/link";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "AI-era capabilities" };
const AREAS = [
  ["Understanding AI", "What these tools can and cannot do, and where they fail."],
  ["Prompting and workflows", "Asking clearly, checking, and building repeatable steps."],
  ["Verification", "Catching wrong or invented answers before you rely on them."],
  ["Privacy and ethics", "What not to paste into a tool, and when to say it was used."],
  ["Human judgement", "Deciding what matters, weighing trade-offs, taking responsibility."],
  ["Communication and creativity", "Explaining, persuading and making things that are yours."],
  ["Domain depth", "Knowing your subject well enough to notice when a tool is wrong."],
  ["Working with people and AI", "Sharing the work, crediting it honestly, learning from each other."],
];
export default function Page() {
  return (<><PageHead title="AI-era capability map" lead="Eight areas that matter whatever your field. Use it to choose what to practise. It makes no claim about which jobs are safe." crumbs={[{ href: "/learn", label: "Learn" }]} />
    <Section><ul className="grid max-w-3xl gap-3 sm:grid-cols-2">{AREAS.map(([a, b]) => <li key={a} className="rounded-md border border-ink/10 bg-white p-4"><p className="font-medium">{a}</p><p className="text-sm text-slate">{b}</p></li>)}</ul>
      <p className="mt-6 flex flex-wrap gap-x-6 gap-y-2"><Link className="text-electric-blue underline" href="/academy?pillar=ai-era">Lessons</Link><Link className="text-electric-blue underline" href="/practise/cases?pillar=ai_vs_human">AI versus human challenges</Link><Link className="text-electric-blue underline" href="/learn/plan">My capability profile</Link></p>
      <p className="mt-4 text-sm text-slate">Which tasks AI changes is moving fast. Any claim about a particular job is dated, sourced and reviewed before it is published here.</p></Section></>);
}

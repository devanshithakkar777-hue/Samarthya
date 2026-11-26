import type { Metadata } from "next";
import Link from "next/link";
import Calculators from "@/components/live/Calculators";
import Hub from "@/components/Hub";

export const metadata: Metadata = { title: "Live" };
export default function Page() {
  return (
    <Hub dest="live" title="Live" lead="Money, everyday skills and looking after yourself. Life comes before productivity."
      extra={<><p className="mt-8"><Link className="text-lg text-electric-blue underline" href="/live/wellness">Wellbeing: support, helplines and a private journal</Link></p><p className="mt-2"><Link className="text-lg text-electric-blue underline" href="/live/presence">Occasion checklists: interviews, calls, first days</Link></p><p className="mt-2"><Link className="text-lg text-electric-blue underline" href="/live/scam-check">Scam checker for job, internship and scholarship messages</Link></p>
        <h2 className="mb-4 mt-10 text-2xl font-semibold">Money calculators</h2><Calculators />
        <p className="mt-8 text-sm text-slate">Lessons on money, housing, safety and everyday life live in the <Link className="text-electric-blue underline" href="/academy?pillar=life-skills">Academy</Link>.</p></>} />
  );
}

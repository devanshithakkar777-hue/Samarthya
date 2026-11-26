import type { Metadata } from "next";
import Link from "next/link";
import Hub from "@/components/Hub";
import Calculators from "@/components/live/Calculators";

export const metadata: Metadata = { title: "Grow" };
const L = "text-electric-blue underline";
export default function Page() {
  return (
    <Hub dest="grow" title="Grow" lead="For the years after the first job: doing well at work, being promoted fairly, switching paths and starting something of your own. Educational guidance only, never a promise about pay or promotion."
      extra={<>
        <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-lg">
          <li><Link className={L} href="/build/growth">Career growth log and 30-60-90 plan</Link></li>
          <li><Link className={L} href="/explore/career-switch">Career switch advisor</Link></li>
          <li><Link className={L} href="/build/venture">Venture tracker</Link></li>
          <li><Link className={L} href="/academy?pillar=growth">Growth lessons</Link></li>
          <li><Link className={L} href="/academy?pillar=entrepreneurship">Entrepreneurship lessons</Link></li>
        </ul>
        <h2 className="mb-2 mt-10 text-2xl font-semibold">Offer and CTC calculators</h2>
        <p className="mb-4 max-w-2xl text-slate">Break a CTC into monthly pay and compare two offers. Educational, not tax or legal advice.</p>
        <Calculators />
      </>} />
  );
}

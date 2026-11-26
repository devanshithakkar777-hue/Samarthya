import type { Metadata } from "next";
import Link from "next/link";
import Hub from "@/components/Hub";
import Master from "@/components/build/Master";
import Private from "@/components/kit/Private";

export const metadata: Metadata = { title: "My journey" };
const L = "text-electric-blue underline";
export default function Page() {
  return (
    <Hub dest="journey" title="My journey" lead="Everything here is private to you. One honest profile of you, turned into resumes, interview confidence and a portfolio you control."
      extra={<><ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-lg"><li><Link className={L} href="/dashboard">My path (dashboard)</Link></li><li><Link className={L} href="/roadmap">Year-by-year roadmap</Link></li><li><Link className={L} href="/progress">Progress</Link></li><li><Link className={L} href="/build/resumes">Resumes</Link></li><li><Link className={L} href="/build/venture">Venture tracker</Link></li><li><Link className={L} href="/build/credentials">Partner credentials</Link></li><li><Link className={L} href="/build/defence">Resume defence practice</Link></li><li><Link className={L} href="/build/portfolio">Portfolio and branding</Link></li><li><Link className={L} href="/practise/open">Interview questions</Link></li><li><Link className={L} href="/build/growth">Career growth log</Link></li><li><Link className={L} href="/companion">Companion</Link></li></ul>
        <h2 className="mb-4 mt-10 text-2xl font-semibold">Your master profile</h2><Private><Master /></Private></>} />
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Footer() {
  const path = usePathname();
  return (
    <footer className="on-dark bg-deep-space text-cool-silver">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-12 md:grid-cols-3">
        <div>
          <p className="text-lg font-semibold text-arctic-white">Samarthya</p>
          <p className="mt-2 text-sm">Every Potential Deserves an Opportunity. Free for every student, with no ads and no paywalls on essentials.</p>
        </div>
        <nav aria-label="Footer" className="grid gap-2 text-sm">
          <Link className="hover:text-cyan" href="/explore">Explore careers</Link>
          <Link className="hover:text-cyan" href="/ask">Ask a sourced question</Link>
          <Link className="hover:text-cyan" href="/live/wellness">Feeling overwhelmed? Support and helplines</Link>
          <Link className="hover:text-cyan" href="/participate">Become part of Samarthya</Link>
          <Link className="hover:text-cyan" href="/about/data">How our information is sourced</Link>
          <Link className="font-medium text-cyan underline" href={`/report?page=${encodeURIComponent(path)}`}>Report wrong information on this page</Link>
          <Link className="hover:text-cyan" href="/privacy">Privacy and your data</Link>
          <Link className="hover:text-cyan" href="/accessibility">Accessibility</Link>
        </nav>
        <p className="text-sm">
          <strong className="text-arctic-white">In immediate danger, call 112.</strong> Free, confidential emotional support is listed on the <Link className="text-cyan underline" href="/live/wellness">wellbeing page</Link>.<br /><br />
          Samarthya shows sourced, dated information and links to official pages. It does not guarantee admission, jobs or outcomes.
          Always confirm details on the official page before you act.
        </p>
      </div>
    </footer>
  );
}

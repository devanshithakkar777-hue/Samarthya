import type { Metadata } from "next";
import Link from "next/link";
import Hub from "@/components/Hub";

export const metadata: Metadata = { title: "Practise" };
const L = "text-electric-blue underline";
export default function Page() {
  return (
    <Hub dest="practise" title="Practise" lead="Rehearse the real thing in private. Practice never ranks you against anyone."
      extra={<ul className="mt-8 grid gap-2 text-lg"><li><Link className={L} href="/practise/tools">Jugaad Lab: tools worth knowing</Link></li><li><Link className={L} href="/practise/drill">Adaptive question practice</Link></li><li><Link className={L} href="/practise/mock-interview">Mock interview (voice or text)</Link></li><li><Link className={L} href="/practise/open">Open questions: interview, case and viva prompts</Link></li>
        <li><Link className={L} href="/practise/cases">Cases and Jugaad challenges</Link></li><li><Link className={L} href="/practise/assessments">Assessments</Link></li><li><Link className={L} href="/progress">My progress and badges</Link></li></ul>} />
  );
}

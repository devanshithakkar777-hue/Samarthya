import type { Metadata } from "next";
import Link from "next/link";
import Hub from "@/components/Hub";

export const metadata: Metadata = { title: "Learn" };

export default function Page() {
  return (
    <Hub dest="learn" title="Learn" lead="Foundations, skills, readings and study tools, free for everyone."
      extra={<p className="mt-8 text-slate">Study tools that are just yours: <Link className="text-electric-blue underline" href="/learn/plan">My learning plan</Link> · <Link className="text-electric-blue underline" href="/learn/elocution">Speaking with confidence</Link> · <Link className="text-electric-blue underline" href="/learn/ai-era">AI-era capability map</Link> · <Link className="text-electric-blue underline" href="/study">notes, flashcards and a study planner</Link>. <Link className="text-electric-blue underline" href="/for-you">What to learn next</Link>. <Link className="text-electric-blue underline" href="/learn/speaking">Speaking practice</Link>. <Link className="text-electric-blue underline" href="/learn/cite">Citation helper</Link>. <Link className="text-electric-blue underline" href="/learn/study-assistant">Study assistant</Link>. <Link className="text-electric-blue underline" href="/learn/notes">Library notes</Link>. <Link className="text-electric-blue underline" href="/learn/concept-maps">Concept maps</Link>.</p>} />
  );
}

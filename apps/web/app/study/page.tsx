import type { Metadata } from "next";
import { PageHead, Section } from "@/components/ui";
import Private from "@/components/kit/Private";
import StudyTabs from "@/components/study/StudyTabs";

export const metadata: Metadata = { title: "Study tools" };

export default function Page() {
  return (<><PageHead title="Study tools" lead="Notes, flashcards that return at the right time, and a planner for assignments and exams. All private to you." crumbs={[{ href: "/learn", label: "Learn" }]} />
    <Section><Private><StudyTabs /></Private></Section></>);
}

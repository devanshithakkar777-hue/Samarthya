import type { Metadata } from "next";
import { StudyAssistant } from "@/components/more/Study";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Study assistant" };
export default function Page() {
  return (<><PageHead title="Study assistant" lead="Ask a question and get an answer from sourced pages and your own notes, with the sources shown." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Private><StudyAssistant /></Private></Section></>);
}

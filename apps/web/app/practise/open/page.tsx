import type { Metadata } from "next";
import Private from "@/components/kit/Private";
import OpenPractice from "@/components/practise/OpenPractice";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Open questions" };
export default async function Page({ searchParams }: { searchParams: Promise<{ pillar?: string }> }) {
  const sp = await searchParams;
  return (<><PageHead title="Open questions" lead="Write your answer, then compare it with what a strong answer covers. Nothing is scored by a machine; you stay the judge." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section><Private><OpenPractice pillar={sp.pillar === "case-knowledge" ? "case-knowledge" : "interview"} /></Private></Section></>);
}

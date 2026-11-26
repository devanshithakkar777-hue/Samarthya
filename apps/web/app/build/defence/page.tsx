import type { Metadata } from "next";
import Defence from "@/components/build/Defence";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Resume defence" };
export default async function Page({ searchParams }: { searchParams: Promise<{ resume?: string }> }) {
  const sp = await searchParams;
  return (<><PageHead title="Resume defence" lead="Be ready to explain everything you wrote. Practise the questions an interviewer could ask about your own resume." crumbs={[{ href: "/build", label: "Build" }]} />
    <Section><Private><Defence resume={sp.resume && /^\d+$/.test(sp.resume) ? sp.resume : undefined} /></Private></Section></>);
}

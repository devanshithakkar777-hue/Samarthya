import type { Metadata } from "next";
import Drill from "@/components/practise/Drill";
import Private from "@/components/kit/Private";
import { apiTry } from "@/lib/api";
import { PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Question practice" };
export default async function Page({ searchParams }: { searchParams: Promise<{ pillar?: string; topic?: string }> }) {
  const sp = await searchParams;
  const meta = await apiTry<{ pillars: Record<string, string> }>("/v1/meta", { pillars: {} }, 300);
  const pillar = sp.pillar && meta.pillars[sp.pillar] ? sp.pillar : Object.keys(meta.pillars)[0] ?? "";
  return (<><PageHead title="Question practice" lead="Questions adjust to you: they get a little harder when you are doing well and easier when you are not. Each answer comes with an explanation." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section><Private><Drill pillar={pillar} topic={sp.topic} pillars={meta.pillars} /></Private></Section></>);
}

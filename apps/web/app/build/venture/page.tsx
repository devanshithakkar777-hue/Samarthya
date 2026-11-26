import type { Metadata } from "next";
import { Ventures } from "@/components/more/Business";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Venture tracker" };
export default function Page() {
  return (<><PageHead title="Venture tracker" lead="For student entrepreneurs: track your idea, stage and milestones privately." crumbs={[{ href: "/build", label: "Build" }]} /><Section><Private><Ventures /></Private></Section></>);
}

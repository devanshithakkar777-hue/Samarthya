import type { Metadata } from "next";
import Capability from "@/components/more/Capability";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "My learning plan" };
export default function Page() {
  return (<><PageHead title="My learning plan and capability profile" lead="Built from the practice questions you answer. It shows where to spend time next. There is no overall score and nobody else can see it." crumbs={[{ href: "/learn", label: "Learn" }]} />
    <Section><Private><Capability /></Private></Section></>);
}

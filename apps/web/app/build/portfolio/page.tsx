import type { Metadata } from "next";
import Portfolio from "@/components/build/Portfolio";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Portfolio and branding" };
export default function Page() {
  return (<><PageHead title="Portfolio and branding" lead="Show your work on a page you control, and tidy how you appear online." crumbs={[{ href: "/build", label: "Build" }]} />
    <Section><Private><Portfolio /></Private></Section></>);
}

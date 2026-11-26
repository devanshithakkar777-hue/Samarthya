import type { Metadata } from "next";
import Private from "@/components/kit/Private";
import ParentLinks from "@/components/ParentLinks";
import Progress from "@/components/Progress";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "My progress" };
export default function Page() {
  return (<><PageHead title="My progress" lead="Your own growth, in your own time. Never ranked. Shared only if you choose to." crumbs={[{ href: "/practise", label: "Practise" }]} />
    <Section><Private><Progress /></Private></Section>
    <Section title="Share with a parent or guardian (optional)"><Private><ParentLinks /></Private></Section></>);
}

import type { Metadata } from "next";
import Applications from "@/components/explore/Applications";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "My applications" };
export default function Page() {
  return (<><PageHead title="My applications" lead="One place for every application: status, deadlines, follow-ups and notes. Private to you." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section><Private><Applications /></Private></Section></>);
}

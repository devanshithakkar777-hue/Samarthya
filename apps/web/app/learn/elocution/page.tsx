import type { Metadata } from "next";
import Elocution from "@/components/learn/Elocution";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Elocution and confidence" };
export default function Page() {
  return (<><PageHead title="Speaking with confidence" lead="A six-step programme and four practice simulators. Private, unrecorded, and never judging your accent." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Elocution /></Section></>);
}

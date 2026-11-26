import type { Metadata } from "next";
import { GroupSessions } from "@/components/more/Business";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Group mentoring sessions" };
export default function Page() {
  return (<><PageHead title="Group mentoring sessions" lead="Join small group sessions run by approved volunteer mentors." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><GroupSessions /></Private></Section></>);
}

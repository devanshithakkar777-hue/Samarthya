import type { Metadata } from "next";
import { ProfessionalDashboard } from "@/components/more/Business";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Mentor dashboard" };
export default function Page() {
  return (<><PageHead title="Mentor dashboard" lead="For approved mentors: requests, sessions and seat counts." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><ProfessionalDashboard /></Private></Section></>);
}

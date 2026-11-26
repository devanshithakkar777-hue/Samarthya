import type { Metadata } from "next";
import { EmployerDashboard } from "@/components/more/Business";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Employer dashboard" };
export default function Page() {
  return (<><PageHead title="Employer dashboard" lead="For approved employers: submit opportunities for review and see anonymous counts." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><EmployerDashboard /></Private></Section></>);
}

import type { Metadata } from "next";
import InstitutionStudent from "@/components/connect/InstitutionStudent";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Your institution" };
export default function Page() {
  return (<><PageHead title="Your institution" lead="Link your college or university if you want, and choose whether to be counted in its totals. You stay in control." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><InstitutionStudent /></Private></Section></>);
}

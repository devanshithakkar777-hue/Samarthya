import type { Metadata } from "next";
import TeamStrengths from "@/components/more/TeamStrengths";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Team strengths map" };
export default function Page() {
  return (<><PageHead title="Team strengths map" lead="See what your team covers and what it does not, before you start a project together." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><TeamStrengths /></Section></>);
}

import type { Metadata } from "next";
import Mentors from "@/components/connect/Mentors";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Mentors" };
export default function Page() {
  return (<><PageHead title="Mentors" lead="Volunteer mentors from industry, alumni, academia, research and entrepreneurship. Ask for guidance, or offer it." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><Mentors /></Private></Section></>);
}

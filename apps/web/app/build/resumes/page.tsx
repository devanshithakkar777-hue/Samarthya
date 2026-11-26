import type { Metadata } from "next";
import ResumeList from "@/components/build/ResumeList";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Resumes" };
export default function Page() {
  return (<><PageHead title="Resumes" lead="Make as many versions as you need from one master profile. Each keeps its history so you can go back." crumbs={[{ href: "/build", label: "Build" }]} />
    <Section><Private><ResumeList /></Private></Section></>);
}

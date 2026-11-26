import type { Metadata } from "next";
import { MockInterviewer } from "@/components/more/Practice";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Mock interview" };
export default function Page() {
  return (<><PageHead title="Mock interview" lead="Practise interview questions by voice or text and get feedback on structure. Private to you." crumbs={[{ href: "/practise", label: "Practise" }]} /><Section><Private><MockInterviewer /></Private></Section></>);
}

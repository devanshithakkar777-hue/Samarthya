import type { Metadata } from "next";
import Companion from "@/components/Companion";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Companion" };
export default function Page() {
  return (<><PageHead title="Companion" lead="A guide that answers from Samarthya's sourced pages and shows where each answer came from." crumbs={[{ href: "/build", label: "Build" }]} /><Section><Private><Companion /></Private></Section></>);
}

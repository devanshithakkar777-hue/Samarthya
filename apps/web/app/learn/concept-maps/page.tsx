import type { Metadata } from "next";
import { ConceptMaps } from "@/components/more/Study";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Concept maps" };
export default function Page() {
  return (<><PageHead title="Concept maps" lead="Draw how ideas connect: add boxes, link them, and save the map privately." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Private><ConceptMaps /></Private></Section></>);
}

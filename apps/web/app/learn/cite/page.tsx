import type { Metadata } from "next";
import Cite from "@/components/learn/Cite";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Citation helper" };
export default function Page() {
  return (<><PageHead title="Citation helper" lead="Format a reference in APA, MLA or Harvard. Crediting sources is part of honest academic work." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Cite /></Section></>);
}

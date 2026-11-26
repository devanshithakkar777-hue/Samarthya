import type { Metadata } from "next";
import { Credentials } from "@/components/more/Business";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Partner credentials" };
export default function Page() {
  return (<><PageHead title="Partner credentials" lead="Credentials issued to you by partner organisations, with a link to their own record." crumbs={[{ href: "/build", label: "Build" }]} /><Section><Private><Credentials /></Private></Section></>);
}

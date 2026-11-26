import type { Metadata } from "next";
import ScamCheck from "@/components/live/ScamCheck";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Scam checker" };
export default function Page() {
  return (<><PageHead title="Scam checker" lead="Fake internships, job offers and scholarships target students. Check a message before you pay, click or share anything." crumbs={[{ href: "/live", label: "Live" }]} />
    <Section><ScamCheck /></Section></>);
}

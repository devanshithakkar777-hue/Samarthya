import type { Metadata } from "next";
import GrowthSummary from "@/components/build/GrowthSummary";
import Radar from "@/components/build/Radar";
import Master from "@/components/build/Master";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Career growth log" };
export default function Page() {
  return (<><PageHead title="Career growth log" lead="Keep a 30-60-90 day plan, KPIs and OKRs, promotion readiness checks, six-month reviews and a leadership log here, next to wins and feedback. After you are hired, keep a record of wins, feedback, new responsibilities and learning. It makes reviews, raises and the next resume far easier." crumbs={[{ href: "/build", label: "Build" }]} />
    <Section><Private><GrowthSummary /><Radar /><Master mode="growth" /></Private></Section></>);
}

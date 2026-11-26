import type { Metadata } from "next";
import { AddPay, PayRanges } from "@/components/more/Community";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Pay ranges" };
export default function Page() {
  return (<><PageHead title="Pay ranges, reported by people" lead="Volunteered by students and workers. A range shows only when ten or more people reported for the same role. It is not a promise of what you will be offered." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section><PayRanges /><h2 className="mb-3 mt-10 text-2xl font-semibold">Add your own figure</h2><Private><AddPay /></Private></Section></>);
}

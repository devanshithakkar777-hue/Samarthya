import type { Metadata } from "next";
import StudyAbroad from "@/components/more/StudyAbroad";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Study abroad cost planner" };
export default function Page() {
  return (<><PageHead title="Study abroad: plan the money" lead="Work out the total cost, what is left to arrange and what a loan would cost each month." crumbs={[{ href: "/explore", label: "Explore" }]} /><Section><StudyAbroad /></Section></>);
}

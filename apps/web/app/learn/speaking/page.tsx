import type { Metadata } from "next";
import Speaking from "@/components/learn/Speaking";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Speaking practice" };
export default function Page() {
  return (<><PageHead title="Speaking practice" lead="Practise pronunciation, pace and confident speaking with your own voice. Private by design: nothing is saved." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Speaking /></Section></>);
}

import type { Metadata } from "next";
import { MyFeedback } from "@/components/more/Community";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Peer feedback" };
export default function Page() {
  return (<><PageHead title="Peer feedback and retrospectives" lead="Private, kind, specific feedback from the people you worked with. No public ratings, ever." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><MyFeedback /></Private></Section></>);
}

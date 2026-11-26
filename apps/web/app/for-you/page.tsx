import type { Metadata } from "next";
import ForYou from "@/components/ForYou";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "What to learn next" };
export default function Page() {
  return (<><PageHead title="What to learn next" lead="Suggestions from your saved roles, your own skills and your practice results. Every suggestion says why." crumbs={[{ href: "/learn", label: "Learn" }]} />
    <Section><Private why="Suggestions are built from your own saved roles and practice, so they need an account."><ForYou /></Private></Section></>);
}

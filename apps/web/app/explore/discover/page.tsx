import type { Metadata } from "next";
import Discover from "@/components/explore/Discover";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Discover your interests" };
export default function Page() {
  return (<><PageHead title="Discover your interests" lead="Thirty-six quick questions about what you would enjoy doing. It gives you a starting list of directions to explore. It is not a test and it does not decide anything." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section><Discover /></Section></>);
}

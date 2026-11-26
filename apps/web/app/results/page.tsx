import type { Metadata } from "next";
import Results from "@/components/Results";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Your options" };

export default function ResultsPage() {
  return (
    <>
      <PageHead title="Your options" lead="Four separate answers for every career. We never merge them into one score, because each tells you something different." />
      <Section><Results /></Section>
    </>
  );
}

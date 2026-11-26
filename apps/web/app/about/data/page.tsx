import type { Metadata } from "next";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "How our information is sourced" };

export default function Page() {
  return (
    <>
      <PageHead title="How our information is sourced" lead="You should never have to trust us blindly." />
      <Section>
        <ol className="grid max-w-3xl list-decimal gap-4 pl-6 text-lg">
          <li>Every fact is tied to a named source and the date we last checked it. Pages show both.</li>
          <li>Nothing goes live until a second person, who did not write it, reviews it against the source.</li>
          <li>Facts that have not been re-checked for about six months are flagged as possibly out of date.</li>
          <li>Requirements are labelled by how strong the evidence is: required, commonly preferred, recommended, or a stand-out extra.</li>
          <li>We show four separate answers about fit and never combine them into a score. Matching uses clear rules, not hidden algorithms.</li>
          <li>We link to official hiring pages only after checking them. We do not take fees or placements.</li>
          <li>Spotted a mistake? <a className="text-electric-blue underline" href="/report">Report it</a>.</li>
        </ol>
      </Section>
    </>
  );
}

import type { Metadata } from "next";
import Presence from "@/components/live/Presence";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Presence checklists" };
export default function Page() {
  return (<><PageHead title="Be ready: occasion checklists" lead="A calm checklist for interviews, calls, presentations and first days. Neatness and preparation, never anyone's looks." crumbs={[{ href: "/live", label: "Live" }]} /><Section><Presence /></Section></>);
}

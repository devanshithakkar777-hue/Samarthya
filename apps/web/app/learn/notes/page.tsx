import type { Metadata } from "next";
import { LibraryNotes } from "@/components/more/Study";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Library notes and highlights" };
export default function Page() {
  return (<><PageHead title="Library notes and highlights" lead="Keep your own notes and short highlights on library items. The books stay on their own sites; only what you type is saved, and only you can see it." crumbs={[{ href: "/learn", label: "Learn" }]} /><Section><Private><LibraryNotes /></Private></Section></>);
}

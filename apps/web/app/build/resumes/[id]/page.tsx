import type { Metadata } from "next";
import ResumeEditor from "@/components/build/ResumeEditor";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Edit resume" };
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (<><PageHead title={id === "new" ? "New resume" : "Edit resume"} lead="Choose what goes in, check it, download it. Every line must be true and something you can talk about." crumbs={[{ href: "/build", label: "Build" }, { href: "/build/resumes", label: "Resumes" }]} />
    <Section><Private><ResumeEditor id={/^(new|\d+)$/.test(id) ? id : "new"} /></Private></Section></>);
}

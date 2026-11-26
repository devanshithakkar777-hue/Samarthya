import type { Metadata } from "next";
import InstitutionStaff from "@/components/connect/InstitutionStaff";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Institution overview", robots: { index: false } };
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return (<><PageHead title="Institution overview" lead="Totals only, for groups of 10 or more students who chose to share. No names and no individual data." crumbs={[{ href: "/institution", label: "Institution" }]} /><Section><Private><InstitutionStaff slug={slug} /></Private></Section></>);
}

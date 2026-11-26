import type { Metadata } from "next";
import EntityList from "@/components/admin/EntityList";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Content workspace", robots: { index: false } };

export default async function Page({ params }: { params: Promise<{ entity: string }> }) {
  const { entity } = await params;
  return (<><PageHead title="Content workspace" crumbs={[{ href: "/admin", label: "Workspace" }]} /><Section><EntityList entity={entity} /></Section></>);
}

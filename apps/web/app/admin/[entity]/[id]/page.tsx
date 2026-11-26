import type { Metadata } from "next";
import EntityEditor from "@/components/admin/EntityEditor";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Edit content", robots: { index: false } };

export default async function Page({ params }: { params: Promise<{ entity: string; id: string }> }) {
  const { entity, id } = await params;
  return (<><PageHead title="Edit content" crumbs={[{ href: "/admin", label: "Workspace" }, { href: `/admin/${entity}`, label: "List" }]} /><Section><EntityEditor entity={entity} id={id} /></Section></>);
}

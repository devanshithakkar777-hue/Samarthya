import type { Metadata } from "next";
import ParentView from "@/components/ParentView";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Shared progress", robots: { index: false, follow: false } };
export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (<><PageHead title="Shared progress" lead="A student chose to share this with you." /><Section><ParentView token={token} /></Section></>);
}

import type { Metadata } from "next";
import { GiveFeedback } from "@/components/more/Community";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Give feedback", robots: { index: false } };
export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (<><PageHead title="Give feedback" lead="Two short notes, private to the person who asked." /><Section><Private><GiveFeedback token={token} /></Private></Section></>);
}

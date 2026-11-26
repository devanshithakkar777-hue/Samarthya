import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Post from "@/components/connect/Post";
import Private from "@/components/kit/Private";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Conversation", robots: { index: false } };
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();
  return (<><PageHead title="Conversation" crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><Post id={id} /></Private></Section></>);
}

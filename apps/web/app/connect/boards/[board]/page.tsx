import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Board from "@/components/connect/Board";
import Private from "@/components/kit/Private";
import { apiGet } from "@/lib/api";
import { PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Community board" };
export default async function Page({ params }: { params: Promise<{ board: string }> }) {
  const { board } = await params;
  const meta = await apiGet<{ boards: Record<string, string> }>("/v1/meta", 300);
  const name = meta.boards[board];
  if (!name) notFound();
  return (<><PageHead title={name} lead="Be kind and specific. No contact details, no harassment." crumbs={[{ href: "/connect", label: "Connect" }]} /><Section><Private><Board board={board} name={name} /></Private></Section></>);
}

import type { Metadata } from "next";
import Case from "@/components/practise/Case";
import Private from "@/components/kit/Private";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { PageHead, Section, Source } from "@/components/ui";

type S = { title: string; kind_note: string; brief: string; provenance: Provenance; pillar_label: string };
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { return { title: (await apiGet<S>(`/v1/scenarios/${(await params).slug}`)).title }; }
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const slug = (await params).slug;
  const s = await apiGet<S>(`/v1/scenarios/${slug}`);
  return (<><PageHead title={s.title} lead={s.pillar_label} crumbs={[{ href: "/practise", label: "Practise" }, { href: "/practise/cases", label: "Cases" }]} />
    <Section><Private><Case slug={slug} note={s.kind_note} /></Private><Source p={s.provenance} /></Section></>);
}

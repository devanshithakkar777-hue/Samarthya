import type { Metadata } from "next";
import ImpactMap from "@/components/world/ImpactMap";
import { apiTry } from "@/lib/api";
import { PageHead, Section } from "@/components/ui";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Connect the dots" };
export default async function Page() {
  const d = await apiTry<{ nodes: never[]; edges: never[]; note: string }>("/v1/impact-map", { nodes: [], edges: [], note: "" }, 120);
  return (<><PageHead title="Connect the dots" lead="See how world briefs link through shared topics. Pick one to see what it connects to." crumbs={[{ href: "/world", label: "World" }]} />
    <Section>{d.nodes.length === 0 ? <p className="text-slate">No briefs are published yet, so there is nothing to connect. Briefs appear here after an editor and a reviewer approve them.</p> : <ImpactMap {...d} />}</Section></>);
}

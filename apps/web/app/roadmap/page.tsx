import type { Metadata } from "next";
import RoadmapView from "@/components/RoadmapView";
import { PageHead, Section } from "@/components/ui";
import { apiTry } from "@/lib/api";
import type { Qualification } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Year-by-year roadmap" };

export default async function Page() {
  const quals = await apiTry<Qualification[]>("/v1/qualifications", []);
  return (<><PageHead title="Year-by-year roadmap" lead="What to focus on in each year of your degree, each step with its source." /><Section><RoadmapView quals={quals} /></Section></>);
}

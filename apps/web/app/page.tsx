import StoryProvider from "@/components/home/StoryContext";
import { Arrival, DegreePreview, Ecosystem, Journey, Participate, Philosophy, Problem } from "@/components/home/Sections";
import { apiTry } from "@/lib/api";
import type { Qualification } from "@/lib/types";

export const dynamic = "force-dynamic";
export const revalidate = 60;

export default async function Home() {
  const quals = await apiTry<Qualification[]>("/v1/qualifications", []);
  return (
    <>
      <div className="bg-gradient-to-b from-deep-space via-midnight-navy to-deep-space">
        <StoryProvider>
          <Arrival />
          <Problem />
          <Ecosystem />
          <Journey />
        </StoryProvider>
      </div>
      <DegreePreview quals={quals} />
      <Philosophy />
      <Participate />
    </>
  );
}

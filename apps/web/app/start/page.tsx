import type { Metadata } from "next";
import StartForm from "@/components/StartForm";
import { PageHead, Section } from "@/components/ui";
import { apiTry } from "@/lib/api";
import type { Qualification, SectorCard } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Find my path" };

export default async function Start() {
  const [quals, sectors] = await Promise.all([
    apiTry<Qualification[]>("/v1/qualifications", []),
    apiTry<SectorCard[]>("/v1/sectors", []),
  ]);
  return (
    <>
      <PageHead title="Find my path" lead="Three quick questions. No account needed. Your answers stay on this device unless you choose to save them." />
      <Section><StartForm quals={quals} sectors={sectors} /></Section>
    </>
  );
}

import type { Metadata } from "next";
import { CareerSwitch } from "@/components/more/Business";
import { PageHead, Section } from "@/components/ui";
import { apiTry } from "@/lib/api";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Career-switch roadmap" };
export default async function Page() {
  const roles = await apiTry<{ slug: string; title: string }[]>("/v1/roles", []);
  return (<><PageHead title="Career-switch roadmap" lead="Pick the role you do or study for now and the one you want. See what the second asks for that the first does not, with free resources where we have them." crumbs={[{ href: "/explore", label: "Explore" }]} />
    <Section><CareerSwitch roles={roles.map((r) => ({ slug: r.slug, title: r.title }))} /></Section></>);
}

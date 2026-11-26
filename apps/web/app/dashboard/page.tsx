import type { Metadata } from "next";
import Dashboard from "@/components/Dashboard";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "My path" };

export default function Page() {
  return (<><PageHead title="My path" lead="Where you are and the next few things worth doing." /><Section><Dashboard /></Section></>);
}

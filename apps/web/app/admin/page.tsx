import type { Metadata } from "next";
import AdminHome from "@/components/admin/AdminHome";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Content workspace", robots: { index: false } };

export default function Page() {
  return (<><PageHead title="Content workspace" lead="Write profiles, check them against sources, and publish only what has been reviewed." /><Section><AdminHome /></Section></>);
}

import type { Metadata } from "next";
import Institutions from "@/components/admin/Institutions";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Institutions", robots: { index: false } };
export default function Page() { return (<><PageHead title="Institutions" lead="Create institutions and assign their staff." crumbs={[{ href: "/admin", label: "Workspace" }]} /><Section><Institutions /></Section></>); }

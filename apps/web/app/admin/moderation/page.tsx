import type { Metadata } from "next";
import Moderation from "@/components/admin/Moderation";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Moderation", robots: { index: false } };
export default function Page() { return (<><PageHead title="Moderation" lead="Community reports and mentor approvals." crumbs={[{ href: "/admin", label: "Workspace" }]} /><Section><Moderation /></Section></>); }

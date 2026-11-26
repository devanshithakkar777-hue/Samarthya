import type { Metadata } from "next";
import ReportForm from "@/components/ReportForm";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Report a problem" };

export default function Page() {
  return (<><PageHead title="Report a problem" lead="Found something wrong, outdated or broken? Tell us. Reports go straight to the people who verify facts." /><Section><ReportForm /></Section></>);
}

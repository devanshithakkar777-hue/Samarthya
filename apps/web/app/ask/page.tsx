import type { Metadata } from "next";
import AskBox from "@/components/AskBox";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Ask" };

export default function Page() {
  return (<><PageHead title="Ask" lead="Plain questions, answered only from sourced facts, with the page and source shown." /><Section><AskBox /></Section></>);
}

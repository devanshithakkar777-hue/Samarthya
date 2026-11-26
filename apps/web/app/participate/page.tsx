import type { Metadata } from "next";
import ParticipateForm from "@/components/ParticipateForm";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Become part of Samarthya" };

export default function Page() {
  return (<><PageHead title="Become part of Samarthya" lead="Help make opportunity accessible to everyone. Tell us how you would like to help and we will reply by email." /><Section><ParticipateForm /></Section></>);
}

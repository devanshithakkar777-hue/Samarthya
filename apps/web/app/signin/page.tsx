import type { Metadata } from "next";
import SignIn from "@/components/SignIn";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Save my progress" };

export default function Page() {
  return (<><PageHead title="Save my progress" lead="Sign in with an email code to keep your answers and checklist on every device. What you did on this device comes with you." /><Section><SignIn /></Section></>);
}

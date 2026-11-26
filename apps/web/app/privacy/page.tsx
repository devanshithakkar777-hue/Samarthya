import type { Metadata } from "next";
import PrivacyActions from "@/components/PrivacyActions";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Privacy and your data" };

export default function Page() {
  return (
    <>
      <PageHead title="Privacy and your data" lead="We collect as little as possible and you stay in control." />
      <Section>
        <div className="grid max-w-3xl gap-6 text-lg">
          <p><strong>Without an account:</strong> your degree, interests and checklist ticks stay in your browser on this device. We do not receive them as a profile. To show your options, the answers are sent to our service to calculate results and are not stored.</p>
          <p><strong>With an account:</strong> we store your email, your answers and your checklist progress so they follow you across devices. We use your email only to send sign-in codes.</p>
          <p><strong>Ask:</strong> if you ask a question we cannot answer, we keep the text of that question (never your name, address or device) so we know what to add. Please do not put personal details in questions.</p>
          <p><strong>Offers to help:</strong> if you offer to mentor, contribute or partner, we keep what you send to reply to you.</p>
          <p><strong>What we never do:</strong> sell or share your data, show advertising, send marketing mail, or rank students against each other.</p>
          <p><strong>Your rights:</strong> download everything we hold about you, or delete your account and all its data, at any time, below. Deletion is immediate.</p>
          <p>Samarthya is for students of all ages. If you are under 18, please involve a parent or teacher before creating an account. You can use everything without one.</p>
          <PrivacyActions />
        </div>
      </Section>
    </>
  );
}

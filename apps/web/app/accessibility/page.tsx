import type { Metadata } from "next";
import { PageHead, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Accessibility" };

export default function Page() {
  return (
    <>
      <PageHead title="Accessibility" lead="Samarthya is built to WCAG 2.2 AA, because every student should be able to use it." />
      <Section>
        <ul className="grid max-w-3xl list-disc gap-3 pl-6 text-lg">
          <li>Everything works with a keyboard and a screen reader.</li>
          <li>Text meets AA colour contrast. Colour is never the only signal.</li>
          <li>The 3D effects are decoration only. They switch off automatically if you prefer reduced motion, use data saver, are on a slow connection, or your device is low-powered. Nothing is lost without them.</li>
          <li>Pages are light and work on budget phones and slow networks.</li>
        </ul>
        <p className="mt-6 max-w-3xl text-lg">Something hard to use? Please <a className="text-electric-blue underline" href="/report">tell us</a> and we will fix it.</p>
      </Section>
    </>
  );
}

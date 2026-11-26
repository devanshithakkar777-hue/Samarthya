import "./globals.css";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { StudentProvider } from "@/lib/student";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: { default: "Samarthya: Every Potential Deserves an Opportunity", template: "%s | Samarthya" },
  description:
    "A free public-welfare platform that helps India's students see what their degree can lead to, what each career asks for, and what to do next, with every fact sourced and dated.",
};
export const viewport: Viewport = { themeColor: "#080F20", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <a href="#main" className="skip-link">Skip to main content</a>
        <StudentProvider>
          <Header />
          <main id="main" tabIndex={-1} className="outline-none">{children}</main>
          <Footer />
        </StudentProvider>
      </body>
    </html>
  );
}

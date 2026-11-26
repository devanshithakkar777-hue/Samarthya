"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useStudent } from "@/lib/student";
import { btn } from "@/components/ui";

/** Wraps a page section that needs an account. Shows a clear, kind prompt instead of an error. */
export default function Private({ children, why }: { children: ReactNode; why?: string }) {
  const { ready, user } = useStudent();
  if (!ready) return <p role="status" className="text-slate">Loading…</p>;
  if (!user) {
    return (
      <div className="max-w-xl rounded-[var(--radius-lg)] border border-ink/10 bg-white p-6">
        <h2 className="text-xl font-semibold">Sign in to use this</h2>
        <p className="mt-2 text-slate">{why ?? "This part saves your own work, so it needs an account. It is free, and you can delete everything at any time."}</p>
        <Link href="/signin" className={`${btn} mt-4`}>Sign in with email</Link>
      </div>
    );
  }
  return <>{children}</>;
}

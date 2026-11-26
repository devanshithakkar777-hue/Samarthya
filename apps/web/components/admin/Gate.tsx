"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useStudent } from "@/lib/student";

export const STAFF = ["editor", "reviewer", "admin"];

export default function Gate({ children, need = STAFF }: { children: (role: string) => ReactNode; need?: string[] }) {
  const { ready, user } = useStudent();
  if (!ready) return <p role="status">Loading…</p>;
  if (!user) return <p>Please <Link className="text-electric-blue underline" href="/signin">sign in</Link> with your editor email.</p>;
  if (!need.includes(user.role)) return <p role="alert" className="rounded bg-ink p-4 text-arctic-white">Your account does not have access to this area.</p>;
  return <>{children(user.role)}</>;
}

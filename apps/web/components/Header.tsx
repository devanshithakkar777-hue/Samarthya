"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useStudent } from "@/lib/student";
import SoundSwitch from "@/components/SoundSwitch";

import { DEST } from "@/lib/nav";

const NAV = [
  ...DEST.map((d) => ({ href: d.href, label: d.name })),
  { href: "/companion", label: "Companion" },
  ];

export default function Header() {
  const path = usePathname();
  const { user, signOut } = useStudent();
  const [open, setOpen] = useState(false);
  const home = path === "/";
  return (
    <header className={`${home ? "absolute inset-x-0 top-0 z-30 on-dark text-arctic-white" : "bg-deep-space text-arctic-white on-dark"}`}>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link href="/" className="text-xl font-semibold tracking-tight" aria-label="Samarthya home">
          Samarthya <span className="sr-only">Every Potential Deserves an Opportunity</span>
        </Link>
        <button
          className="rounded-md border border-cool-silver/40 px-3 py-2 text-sm md:hidden"
          aria-expanded={open} aria-controls="site-nav" onClick={() => setOpen((v) => !v)}
        >
          {open ? "Close" : "Menu"}
        </button>
        <nav id="site-nav" aria-label="Main" className={`${open ? "flex" : "hidden"} absolute left-0 right-0 top-full flex-col gap-1 bg-deep-space p-5 md:static md:flex md:flex-row md:items-center md:gap-5 md:bg-transparent md:p-0`}>
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} onClick={() => setOpen(false)}
              aria-current={path.startsWith(n.href) ? "page" : undefined}
              className={`rounded px-2 py-2 text-sm hover:text-cyan ${path.startsWith(n.href) ? "text-cyan" : "text-cool-silver"}`}>
              {n.label}
            </Link>
          ))}
          {user && ["editor", "reviewer", "admin"].includes(user.role) && (
            <Link href="/admin" onClick={() => setOpen(false)} className="rounded px-2 py-2 text-sm text-cool-silver hover:text-cyan">Workspace</Link>
          )}
          <SoundSwitch />
          {user ? (
            <button onClick={() => { void signOut(); setOpen(false); }} className="rounded-md border border-cool-silver/40 px-3 py-2 text-left text-sm text-cool-silver hover:text-cyan">
              Sign out
            </button>
          ) : (
            <Link href="/signin" onClick={() => setOpen(false)} className="rounded-md bg-cyan px-4 py-2 text-sm font-medium text-deep-space hover:bg-ice-blue">
              Save my progress
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}

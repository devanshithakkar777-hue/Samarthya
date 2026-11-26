import Link from "next/link";
import type { ReactNode } from "react";
import type { Provenance } from "@/lib/types";

export function fmtDate(iso: string | null | undefined) {
  if (!iso) return "date not recorded";
  return new Date(iso).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" });
}

export function Section({ title, children, id, dark }: { title?: string; children: ReactNode; id?: string; dark?: boolean }) {
  return (
    <section id={id} className={dark ? "on-dark bg-midnight-navy text-arctic-white" : ""}>
      <div className="mx-auto max-w-6xl px-5 py-12">
        {title && <h2 className="mb-6 text-2xl font-semibold tracking-tight">{title}</h2>}
        {children}
      </div>
    </section>
  );
}

export function PageHead({ title, lead, crumbs }: { title: string; lead?: string; crumbs?: { href: string; label: string }[] }) {
  return (
    <div className="on-dark bg-deep-space text-arctic-white">
      <div className="mx-auto max-w-6xl px-5 pb-10 pt-8">
        {crumbs && (
          <nav aria-label="Breadcrumb" className="mb-3 text-sm text-cool-silver">
            {crumbs.map((c) => (<span key={c.href}><Link className="hover:text-cyan" href={c.href}>{c.label}</Link> / </span>))}
          </nav>
        )}
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
        {lead && <p className="mt-3 max-w-3xl text-lg text-cool-silver">{lead}</p>}
      </div>
    </div>
  );
}

/** Every fact shows where it came from and when it was last checked. */
export function Source({ p }: { p: Provenance }) {
  return (
    <p className="mt-3 text-sm text-slate">
      {p.source ? (
        <>Source: <a className="text-electric-blue underline" href={p.source.url} target="_blank" rel="noopener noreferrer">{p.source.title}<span className="sr-only"> (opens in a new tab)</span></a>, {p.source.publisher}. </>
      ) : "Source not recorded. "}
      Last checked {fmtDate(p.last_verified)}.
      {p.stale && <strong className="ml-1 rounded bg-ink px-2 py-0.5 text-arctic-white">May be out of date. Check the official page.</strong>}
    </p>
  );
}

export function Card({ href, title, children }: { href: string; title: string; children?: ReactNode }) {
  return (
    <Link href={href} className="group block rounded-[var(--radius-lg)] border border-ink/10 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-electric-blue hover:shadow-md">
      <h3 className="text-lg font-semibold text-ink group-hover:text-electric-blue">{title}</h3>
      {children && <div className="mt-2 text-sm text-slate">{children}</div>}
    </Link>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-dashed border-slate/50 bg-white p-8 text-center">
      <p className="text-lg font-semibold">{title}</p>
      {children && <div className="mt-2 text-slate">{children}</div>}
    </div>
  );
}

export const btn = "inline-flex items-center justify-center rounded-md bg-electric-blue px-5 py-3 font-medium text-arctic-white hover:bg-midnight-navy disabled:opacity-60";
export const btnGhost = "inline-flex items-center justify-center rounded-md border border-electric-blue px-5 py-3 font-medium text-electric-blue hover:bg-electric-blue hover:text-arctic-white";

import type { Metadata } from "next";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { Provenance } from "@/lib/types";
import { Card, PageHead, Section, Source } from "@/components/ui";
import SaveNote from "@/components/SaveNote";

type L = { slug: string; title: string; summary: string; body: string; level: string; minutes: number | null; language: string; track: string; provenance: Provenance; next_in_track: { slug: string; title: string; summary: string }[] };

export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  return { title: (await apiGet<L>(`/v1/lessons/${(await params).slug}`)).title };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const l = await apiGet<L>(`/v1/lessons/${(await params).slug}`);
  return (
    <>
      <PageHead title={l.title} lead={l.summary} crumbs={[{ href: "/learn", label: "Learn" }, { href: "/academy", label: "Academy" }]} />
      <Section>
        <article lang={l.language === "Hindi" ? "hi" : undefined} className="max-w-3xl">
          <p className="mb-4 text-sm text-slate">{l.track} · {l.level}{l.minutes ? ` · about ${l.minutes} minutes` : ""}</p>
          <div className="whitespace-pre-line text-lg leading-relaxed">{l.body}</div>
          <Source p={l.provenance} />
          <SaveNote title={l.title} />
        </article>
        {l.next_in_track.length > 0 && (<><h2 className="mb-3 mt-10 text-xl font-semibold">More in this track</h2>
          <ul className="grid gap-4 md:grid-cols-3">{l.next_in_track.map((n) => <li key={n.slug}><Card href={`/academy/${n.slug}`} title={n.title}>{n.summary}</Card></li>)}</ul></>)}
        <p className="mt-8 text-sm"><Link className="text-electric-blue underline" href="/report">Report a mistake in this lesson</Link></p>
      </Section>
    </>
  );
}

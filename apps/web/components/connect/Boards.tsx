"use client";

import Link from "next/link";
import { useMine } from "@/lib/useMine";
import { Card } from "@/components/ui";
import Handle from "./Handle";

export default function Boards() {
  const b = useMine<{ boards: { slug: string; name: string; posts: number }[]; guidelines: string[] }>("/v1/community/boards");
  return (
    <Handle>{(handle) => (<div><p className="mb-4 text-slate">You are posting as <strong>{handle}</strong>. <Link className="text-electric-blue underline" href="/connect/mentors">Looking for a mentor?</Link></p>
      <ul className="grid gap-4 md:grid-cols-2">{(b.data?.boards ?? []).map((x) => <li key={x.slug}><Card href={`/connect/boards/${x.slug}`} title={x.name}>{x.posts} post{x.posts === 1 ? "" : "s"}</Card></li>)}</ul>
      <h2 className="mb-2 mt-8 text-lg font-semibold">House rules</h2><ul className="list-disc pl-5 text-sm text-slate">{(b.data?.guidelines ?? []).map((g) => <li key={g}>{g}</li>)}</ul></div>)}</Handle>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { DESTINATIONS, ENVIRONMENTS, STAGES } from "@/lib/destinations";
import { call } from "@/lib/client";
import type { FitItem, Qualification } from "@/lib/types";
import { useStory } from "./StoryContext";

const panel = "rounded-[var(--radius-lg)] bg-deep-space/80 p-6 ring-1 ring-cool-silver/20";

export function Arrival() {
  return (
    <section className="on-dark relative min-h-[88vh] text-arctic-white" aria-labelledby="hero-title">
      <div className="mx-auto flex min-h-[88vh] max-w-6xl flex-col justify-center px-5 pb-16 pt-32">
        <p className="mb-4 text-sm uppercase tracking-widest text-cyan">Samarthya</p>
        <h1 id="hero-title" className="max-w-4xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Every Potential Deserves an Opportunity
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-cool-silver md:text-xl">
          A unified ecosystem for learning, discovering opportunities, building capabilities and shaping your future. Free for every student in India.
        </p>
        <div className="mt-8 flex flex-wrap gap-4">
          <a href="#ecosystem" className="inline-flex items-center rounded-md bg-cyan px-5 py-3 font-medium text-deep-space hover:bg-ice-blue">Explore the Ecosystem</a>
          <Link href="/start" className="inline-flex items-center rounded-md border border-cool-silver/60 px-5 py-3 font-medium hover:border-cyan hover:text-cyan">Discover Your Journey</Link>
        </div>
        <p className="mt-4 text-sm text-cool-silver">No sign-up needed. Your answers stay on your device until you choose to save them.</p>
      </div>
    </section>
  );
}

export function Problem() {
  return (
    <section className="on-dark text-arctic-white" aria-labelledby="problem-title">
      <div className="mx-auto max-w-6xl px-5 py-24">
        <h2 id="problem-title" className="max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">Potential is everywhere. Opportunity isn&apos;t.</h2>
        <p className={`${panel} mt-6 max-w-3xl text-lg text-cool-silver`}>
          Education, knowledge, skills, career guidance, practical experience, mentorship and opportunities live in separate places, and few students can see how they connect. Samarthya joins them in one place, free to use.
        </p>
        <ul className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {ENVIRONMENTS.map((e, i) => (
            <li key={e} className="rounded-lg bg-midnight-navy/90 px-4 py-3 ring-1 ring-cool-silver/20" style={{ transform: `translateY(${(i % 3) * 6}px)` }}>{e}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Ecosystem() {
  const { setActive } = useStory();
  const [open, setOpen] = useState<string | null>(null);
  const d = DESTINATIONS.find((x) => x.key === open);
  const badge = (s: string) => (s === "open" ? "Built" : s === "partial" ? "Partly open" : "Opening in stages");
  return (
    <section id="ecosystem" className="on-dark text-arctic-white" aria-labelledby="eco-title">
      <div className="mx-auto max-w-6xl px-5 py-24">
        <h2 id="eco-title" className="text-3xl font-semibold tracking-tight md:text-5xl">Seven destinations</h2>
        <p className={`${panel} mt-6 max-w-3xl text-lg text-cool-silver`}>One platform, organised around seven places instead of thirty menus. Everything is built; content is marked draft until a named reviewer approves it.</p>
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {DESTINATIONS.map((x, i) => (
            <li key={x.key}>
              <button
                aria-expanded={open === x.key} aria-controls="dest-panel"
                onMouseEnter={() => setActive(i)} onFocus={() => setActive(i)} onMouseLeave={() => setActive(-1)} onBlur={() => setActive(-1)}
                onClick={() => setOpen(open === x.key ? null : x.key)}
                className={`h-full w-full rounded-[var(--radius-lg)] bg-midnight-navy/90 p-5 text-left ring-1 transition hover:-translate-y-1 ${open === x.key ? "ring-cyan" : "ring-cool-silver/20"}`}>
                <span className="block text-xl font-semibold">{x.name}</span>
                <span className="mt-1 block text-cool-silver">{x.short}</span>
                <span className={`mt-3 inline-block rounded px-2 py-0.5 text-sm ${x.state === "later" ? "bg-deep-space text-ice-blue ring-1 ring-ice-blue/40" : "bg-cyan text-deep-space"}`}>{badge(x.state)}</span>
              </button>
            </li>
          ))}
        </ul>
        <div id="dest-panel" aria-live="polite" className="mt-6">
          {d && (
            <div className={`${panel} grid gap-3`}>
              <h3 className="text-2xl font-semibold">{d.name}</h3>
              <p className="text-cool-silver">{d.contains}</p>
              <p><strong>Today:</strong> {d.now}</p>
              <p><strong>Later:</strong> {d.later}</p>
              {d.href && <p><Link className="text-cyan underline" href={d.href}>Go to {d.name}</Link></p>}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export function Journey() {
  const path = useRef<SVGPathElement>(null);
  const { tier } = useStory();
  useEffect(() => {
    // draw the path as it scrolls into view; without motion it is simply fully drawn
    const el = path.current; if (!el || tier === "off") return;
    const len = el.getTotalLength(); el.style.strokeDasharray = String(len);
    let raf = 0;
    const tick = () => {
      const r = el.getBoundingClientRect(); const vh = window.innerHeight;
      const t = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height * 0.5)));
      el.style.strokeDashoffset = String(len * (1 - t)); raf = 0;
    };
    const on = () => { if (!raf) raf = requestAnimationFrame(tick); };
    tick(); window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, [tier]);
  return (
    <section className="on-dark text-arctic-white" aria-labelledby="journey-title">
      <div className="mx-auto max-w-6xl px-5 py-24">
        <h2 id="journey-title" className="max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">Your journey doesn&apos;t end with a degree. Neither should your opportunities.</h2>
        <svg viewBox="0 0 1000 120" className="mt-10 hidden w-full md:block" role="img" aria-label="A winding path through seven connected stages">
          <path ref={path} d="M20 80 C 170 10, 250 110, 400 60 S 650 10, 760 60 S 920 100, 980 40" fill="none" stroke="#36B9E9" strokeWidth="3" strokeLinecap="round" />
          {STAGES.map((s, i) => (<circle key={s} cx={20 + (i * 960) / 6} cy={i % 2 ? 62 : 70} r="7" fill="#F2F6FC" />))}
        </svg>
        <ol className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-7">
          {STAGES.map((s, i) => (<li key={s} className="rounded-lg bg-midnight-navy/90 px-4 py-3 ring-1 ring-cool-silver/20"><span className="text-sm text-cyan">{i + 1}</span><br />{s}</li>))}
        </ol>
        <p className={`${panel} mt-6 max-w-3xl text-cool-silver`}>These stages are connected, not a single required path. You can enter anywhere and return to any of them.</p>
      </div>
    </section>
  );
}

export function DegreePreview({ quals }: { quals: Qualification[] }) {
  const [slug, setSlug] = useState("");
  const [items, setItems] = useState<FitItem[] | null>(null);
  const [err, setErr] = useState("");
  async function pick(v: string) {
    setSlug(v); setItems(null); setErr("");
    if (!v) return;
    try {
      const r = await call<{ results: FitItem[] }>("POST", "/v1/fit", { profile: { qualification: v, interests: [], skills: [] }, completed_requirement_ids: [], sort: "eligibility" });
      setItems(r.results.filter((x) => x.eligibility.label === "eligible" || x.eligibility.label === "open").slice(0, 4));
    } catch (e) { setErr((e as Error).message); }
  }
  return (
    <section className="on-dark bg-midnight-navy text-arctic-white" aria-labelledby="deg-title">
      <div className="mx-auto max-w-6xl px-5 py-20">
        <h2 id="deg-title" className="text-3xl font-semibold tracking-tight">Try it: what could your degree lead to?</h2>
        {quals.length ? (
          <>
            <label htmlFor="deg" className="mt-6 block font-medium">Pick your degree</label>
            <select id="deg" value={slug} onChange={(e) => pick(e.target.value)} className="mt-1 w-full max-w-md rounded-md bg-arctic-white px-3 py-3 text-ink">
              <option value="">Choose…</option>
              {quals.map((q) => (<option key={q.id} value={q.slug}>{q.degree}{q.specialization ? `, ${q.specialization}` : ""}</option>))}
            </select>
            <div aria-live="polite" className="mt-6">
              {err && <p role="alert">{err}</p>}
              {items && !items.length && <p className="text-cool-silver">We have not published roles for this degree yet. Browse all sectors instead.</p>}
              {items && items.length > 0 && (
                <ul className="grid gap-3 sm:grid-cols-2">
                  {items.map((it) => (
                    <li key={it.role.id} className="rounded-lg bg-deep-space p-4 ring-1 ring-cool-silver/20">
                      <Link className="font-semibold text-cyan underline" href={`/roles/${it.role.slug}`}>{it.role.title}</Link>
                      <span className="block text-sm text-cool-silver">{it.role.sector.name}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <p className="mt-6"><Link className="text-cyan underline" href={slug ? `/start?q=${slug}` : "/start"}>Get my full, personalised view</Link></p>
          </>
        ) : (
          <p className="mt-4 max-w-2xl text-cool-silver">Degrees are published here once each is reviewed against a source. Until then you can browse careers by sector.</p>
        )}
      </div>
    </section>
  );
}

export function Philosophy() {
  return (
    <section className="bg-arctic-white text-ink" aria-labelledby="phil-title">
      <div className="mx-auto max-w-4xl px-5 py-28 text-center">
        <h2 id="phil-title" className="sr-only">Our philosophy</h2>
        <p className="text-2xl font-medium leading-relaxed text-ink md:text-4xl">Knowledge should empower.</p>
        <p className="mt-4 text-2xl font-medium leading-relaxed text-ink md:text-4xl">Opportunity should be accessible.</p>
        <p className="mt-4 text-2xl font-medium leading-relaxed text-electric-blue md:text-4xl">Potential should never be limited by purchasing power.</p>
      </div>
    </section>
  );
}

const PATHS = [
  ["Learn", "Use Samarthya free, as a student at any stage."],
  ["Mentor", "Share your experience with students when mentoring opens."],
  ["Contribute resources", "Help us source and verify careers, skills and learning resources."],
  ["Collaborate as an institution", "Partner as a college or organisation in the pilot."],
  ["Volunteer", "Offer your time where the platform needs people."],
];
export function Participate() {
  return (
    <section className="on-dark bg-deep-space text-arctic-white" aria-labelledby="part-title">
      <div className="mx-auto max-w-6xl px-5 py-24">
        <h2 id="part-title" className="max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">Help make opportunity accessible to everyone</h2>
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {PATHS.map(([t, d]) => (<li key={t} className="rounded-[var(--radius-lg)] bg-midnight-navy p-5 ring-1 ring-cool-silver/20"><h3 className="font-semibold">{t}</h3><p className="mt-2 text-sm text-cool-silver">{d}</p></li>))}
        </ul>
        <div className="mt-10"><Link href="/participate" className="inline-flex items-center rounded-md bg-cyan px-6 py-3 font-medium text-deep-space hover:bg-ice-blue">Become Part of Samarthya</Link></div>
      </div>
    </section>
  );
}

export type Crisis = { message: string; resources: { name: string; phone: string; alt_phone: string | null; source: string; source_title: string }[] };

/** Shown whenever someone may be in distress. Phone numbers are plain links so they work with one tap. */
export default function CrisisBox({ c, checkedOn }: { c: Crisis; checkedOn?: string }) {
  return (
    <section aria-labelledby="crisis" className="rounded-[var(--radius-lg)] border-2 border-ink bg-white p-5" role="region">
      <h2 id="crisis" className="text-xl font-semibold">If you need to talk to someone now</h2>
      {c.message && <p className="mt-1">{c.message}</p>}
      <ul className="mt-3 grid gap-3">{c.resources.map((r) => (
        <li key={r.name}><p className="font-medium">{r.name}</p>
          <p><a className="text-2xl font-semibold text-electric-blue underline" href={`tel:${r.phone.replace(/[^\d+]/g, "")}`}>{r.phone}</a>{r.alt_phone && <span className="ml-3">or <a className="text-electric-blue underline" href={`tel:${r.alt_phone.replace(/[^\d+]/g, "")}`}>{r.alt_phone}</a></span>}</p>
          <p className="text-xs text-slate">Source: <a className="underline" href={r.source} target="_blank" rel="noopener noreferrer">{r.source_title}<span className="sr-only"> (opens in a new tab)</span></a></p></li>))}</ul>
      <p className="mt-3 text-sm">If you or someone near you is in immediate danger, call <a className="font-semibold underline" href="tel:112">112</a>.{checkedOn ? ` Numbers last checked ${checkedOn}.` : ""}</p>
    </section>
  );
}

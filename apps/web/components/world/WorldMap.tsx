import Link from "next/link";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import atlas from "world-atlas/countries-110m.json";

type Country = { slug: string; name: string; iso_numeric: string };

let cache: { id: string; d: string }[] | null = null;
function shapes() {
  if (cache) return cache;
  const topo = atlas as unknown as Topology;
  const fc = feature(topo, topo.objects.countries) as unknown as GeoJSON.FeatureCollection;
  const proj = geoNaturalEarth1().fitSize([960, 500], fc);
  const gp = geoPath(proj);
  cache = fc.features.map((f) => ({ id: String(f.id ?? "").padStart(3, "0"), d: gp(f) ?? "" })).filter((s) => s.d);
  return cache;
}

/** Server-rendered map: countries with a published page are links; the rest are drawn but inert. No script, works offline. */
export default function WorldMap({ countries }: { countries: Country[] }) {
  const by = new Map(countries.map((c) => [c.iso_numeric.padStart(3, "0"), c]));
  return (
    <figure>
      <svg viewBox="0 0 960 500" role="group" aria-label="World map. Countries with a published page are links." className="h-auto w-full rounded-[var(--radius-lg)] border border-ink/10 bg-white">
        {shapes().map((s) => {
          const c = by.get(s.id);
          return c ? (
            <Link key={s.id} href={`/world/countries/${c.slug}`} aria-label={c.name}><path d={s.d} className="fill-electric-blue stroke-white hover:fill-midnight-navy focus:fill-midnight-navy" strokeWidth={0.5}><title>{c.name}</title></path></Link>
          ) : <path key={s.id} d={s.d} className="fill-cool-silver/50 stroke-white" strokeWidth={0.5} />;
        })}
      </svg>
      <figcaption className="mt-2 text-sm text-slate">{countries.length === 0 ? "No country pages are published yet." : `${countries.length} countr${countries.length === 1 ? "y" : "ies"} with a sourced page. Pick one from the map or the list below.`}</figcaption>
    </figure>
  );
}

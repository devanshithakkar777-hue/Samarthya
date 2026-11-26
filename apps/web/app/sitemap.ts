import type { MetadataRoute } from "next";
import { apiTry } from "@/lib/api";
import type { CompanyCard, RoleCard, SectorCard } from "@/lib/types";

const SITE = process.env.SITE_URL ?? "http://localhost:3000";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [s, r, c, les, opp, br, co] = await Promise.all([
    apiTry<SectorCard[]>("/v1/sectors", []), apiTry<RoleCard[]>("/v1/roles", []), apiTry<CompanyCard[]>("/v1/companies", []),
    apiTry<{ results: { slug: string }[] }>("/v1/lessons", { results: [] }), apiTry<{ results: { slug: string }[] }>("/v1/opportunities", { results: [] }),
    apiTry<{ results: { slug: string }[] }>("/v1/briefs", { results: [] }), apiTry<{ results: { slug: string }[] }>("/v1/countries", { results: [] }),
  ]);
  const fixed = ["/live/scam-check", "/explore/discover", "/world/daily", "/connect/events", "/learn/cite", "/learn/speaking", "/learn", "/practise", "/build", "/live", "/connect", "/academy", "/library", "/skills", "/opportunities", "/world", "/live/wellness", "/practise/cases", "/practise/assessments", "", "/explore", "/pathways", "/companies", "/roadmap", "/briefing", "/start", "/privacy", "/accessibility", "/about/data"];
  return [
    ...fixed.map((p) => ({ url: `${SITE}${p}` })),
    ...s.map((x) => ({ url: `${SITE}/explore/${x.slug}` })),
    ...r.map((x) => ({ url: `${SITE}/roles/${x.slug}` })),
    ...c.map((x) => ({ url: `${SITE}/companies/${x.slug}` })),
    ...les.results.map((x) => ({ url: `${SITE}/academy/${x.slug}` })),
    ...opp.results.map((x) => ({ url: `${SITE}/opportunities/${x.slug}` })),
    ...br.results.map((x) => ({ url: `${SITE}/world/briefs/${x.slug}` })),
    ...co.results.map((x) => ({ url: `${SITE}/world/countries/${x.slug}` })),
  ];
}

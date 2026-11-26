export type Provenance = {
  source: { url: string; title: string; publisher: string; kind: string; published_on: string | null } | null;
  last_verified: string | null;
  stale: boolean;
};

export type Qualification = { id: number; slug: string; degree: string; level: string; kind?: string; stream?: string | null; awarding_body?: string | null; specialization: string | null; duration_years: number | null };
export type SectorCard = { id: number; slug: string; name: string; summary: string; role_count: number };
export type RoleCard = { id: number; slug: string; title: string; job_family: string; level: string; sector: { slug: string; name: string } };
export type Requirement = { id: number; type: string; label: string; note: string | null; skill: { slug: string; name: string } | null };
export type Employer = { company: string; slug: string; careers_url: string; last_verified: string };

export type SectorDetail = SectorCard & Provenance & {
  roles: RoleCard[];
  education_routes: { qualification: { slug: string; degree: string; specialization: string | null }; strength: number; reason: string }[];
};
export type RoleDetail = RoleCard & Provenance & {
  description: string; progression: string | null;
  requirements: Record<"mandatory" | "common_preference" | "recommended" | "differentiator", Requirement[]>;
  entry_degrees: { slug: string; degree: string; specialization: string | null; note: string | null }[];
  employers: Employer[];
};
export type CompanyCard = { id: number; slug: string; name: string; summary: string; listing_status: string | null };
export type CompanyDetail = CompanyCard & Provenance & {
  cin: string | null; industry_code: string | null; website: string | null;
  roles: { slug: string; title: string; careers_url: string; last_verified: string }[];
};
export type Resource = Provenance & {
  id: number; title: string; provider: string; url: string; format: string; level: string; price_inr: number;
  free: boolean; language: string; duration_hours: number | null; certificate: boolean; sponsored: boolean;
};
export type SkillDetail = Provenance & { id: number; slug: string; name: string; category: string; overview: string; resources: Resource[] };
export type Roadmap = {
  qualification: { slug: string; degree: string; duration_years: number | null };
  years: { year: number; steps: ({ id: number; title: string; detail: string } & Provenance)[] }[];
};
export type BriefItem = Provenance & {
  id: number; headline: string; summary: string; why_it_matters: string; link: string; event_date: string;
  sector: { slug: string; name: string } | null;
};
export type Coverage = Record<string, number | string | null>;

export type Answer = { label: string; reasons: string[] };
export type FitItem = {
  role: { id: number; slug: string; title: string; level: string; sector: { slug: string; name: string } } & Provenance;
  eligibility: Answer & { listed_degrees: string[] };
  compatibility: Answer;
  readiness: Answer & {
    by_tier: Record<string, { done: number; total: number }>;
    outstanding: { id: number; label: string; tier: string; type: string }[];
  };
  opportunity: Answer & { hiring_pages: { company: string; company_slug: string; careers_url: string; last_verified: string }[] };
};

export type Profile = {
  qualification: string | null;
  year_of_study: number | null;
  expected_graduation_year: number | null;
  interests: string[];
  skills: string[];
};

export type PathwayItem = { slug: string; name: string; kind: string; stream: string | null; level: string; awarding_body: string | null; duration_years: number | null };
export type PathwayList = { items: PathwayItem[]; total: number; truncated: boolean; streams: Record<string, number>; kinds: Record<string, number> };
export type PathwayDetail = Provenance & {
  slug: string; name: string; kind: string; stream: string | null; level: string; specialization: string | null;
  awarding_body: string | null; duration_years: number | null; not_yet_verified: string[];
  eligibility: string | null; entry_route: string | null; training: string | null; recognition: string | null; cost_note: string | null; official_url: string | null;
  sectors: { slug: string; name: string; reason: string }[]; roles: { slug: string; title: string }[];
};

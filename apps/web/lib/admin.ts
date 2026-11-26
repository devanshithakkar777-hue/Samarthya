export type FieldType = "text" | "textarea" | "number" | "bool" | "date" | "select" | "ref" | "json" | "lines";
export type Field = {
  name: string; label: string; type: FieldType; required?: boolean; help?: string;
  options?: string[]; ref?: string; refLabel?: string;
};
export type Linked = { entity: string; fk: string; title: string; fields: Field[]; summary: string[] };
export type EntityConfig = { key: string; singular: string; plural: string; label: string[]; fields: Field[]; sourced: boolean; linked?: Linked[]; hint?: string };

const T = (name: string, label: string, extra: Partial<Field> = {}): Field => ({ name, label, type: "text", ...extra });
const A = (name: string, label: string, extra: Partial<Field> = {}): Field => ({ name, label, type: "textarea", ...extra });
const slug = T("slug", "Web address name (slug)", { required: true, help: "Lowercase letters, numbers and hyphens, e.g. data-analyst" });

export const TIERS = ["mandatory", "common_preference", "recommended", "differentiator"];
export const REQ_TYPES = ["skill", "subject", "internship", "experience", "certification"];

export const ENTITIES: Record<string, EntityConfig> = {
  roles: {
    key: "roles", singular: "Role", plural: "Roles", label: ["title"], sourced: true,
    hint: "A role profile: plain description, what it asks for, degrees that lead here, and where to look. Keep it short and cite one source.",
    fields: [
      T("title", "Role title", { required: true }), slug,
      { name: "sector_id", label: "Sector (must be published to publish this role)", type: "ref", ref: "sectors", refLabel: "name", required: true },
      T("job_family", "Job family", { required: true }),
      { name: "level", label: "Level", type: "select", options: ["entry", "mid", "senior"], required: true },
      A("description", "What this person does (plain, short)", { required: true }),
      A("progression", "How the career grows"),
    ],
    linked: [
      { entity: "role_requirements", fk: "role_id", title: "What the role asks for (at least one needed to publish)", summary: ["tier", "label"],
        fields: [
          T("label", "Requirement", { required: true }),
          { name: "tier", label: "How strong is the evidence?", type: "select", options: TIERS, required: true, help: "mandatory = required by employers or regulation; common_preference = often listed; recommended = our advice; differentiator = stand-out extra" },
          { name: "type", label: "Type", type: "select", options: REQ_TYPES, required: true },
          { name: "skill_id", label: "Linked skill page (optional)", type: "ref", ref: "skills", refLabel: "name" },
          T("note", "Note"),
          { name: "position", label: "Order", type: "number" },
        ] },
      { entity: "role_qualifications", fk: "role_id", title: "Degrees that can lead here", summary: ["qualification_id", "note"],
        fields: [
          { name: "qualification_id", label: "Degree", type: "ref", ref: "qualifications", refLabel: "degree", required: true },
          T("note", "Note"),
        ] },
    ],
  },
  sectors: {
    key: "sectors", singular: "Sector", plural: "Sectors", label: ["name"], sourced: true,
    fields: [T("name", "Sector name", { required: true }), slug, A("summary", "Summary", { required: true })],
  },
  qualifications: {
    key: "qualifications", singular: "Degree", plural: "Degrees", label: ["degree", "specialization"], sourced: true,
    fields: [
      T("degree", "Degree", { required: true, help: "e.g. B.Tech" }), slug, T("specialization", "Specialization"),
      { name: "kind", label: "Type of qualification", type: "select", options: ["degree", "diploma", "certificate", "professional_qualification", "certification", "licence", "examination"], required: true, help: "A degree, a professional qualification (CA, CFA) and a certification are different things" },
      { name: "stream", label: "Primary stream", type: "select", options: ["Science (PCM)", "Science (PCB)", "Science (PCMB)", "Commerce", "Humanities and Arts", "Vocational", "Engineering and Technology", "Medical and Health Sciences", "Agriculture and Environment", "Law", "Management and Business", "Finance, Banking and Economics", "Architecture, Planning and Design", "Arts, Media and Entertainment", "Education, Public Policy and Public Service", "Aviation", "Merchant Navy", "Defence", "Hospitality", "Tourism", "Sports", "Fitness", "Library and Information Science", "Information and Knowledge Management", "Maritime and Shipping", "Disaster Management", "Urban Development", "Security Studies", "Forensic Studies", "Religious and Indic Studies", "International Development"] },
      T("awarding_body", "Awarding authority", { help: "University, statutory body, institute or certification provider" }),
      A("eligibility", "Eligibility", { help: "Class 12 subjects, minimum marks, age limits, prior qualifications. Only what the source states." }),
      A("entry_route", "Entry route", { help: "Entrance exam, direct admission, foundation examination, etc." }),
      A("training", "Mandatory training and work experience"),
      A("recognition", "Recognition", { help: "Regulatory approval, accreditation, registration" }),
      A("cost_note", "Cost and financial assistance", { help: "Publicly stated fees only" }),
      T("official_url", "Official link", { help: "Awarding body or institution page" }),
      { name: "level", label: "Level", type: "select", options: ["undergraduate", "postgraduate", "doctoral", "diploma", "unspecified"], required: true },
      { name: "duration_years", label: "Duration (years)", type: "number", help: "Leave blank if the source does not state it" },
    ],
    linked: [
      { entity: "qualification_sectors", fk: "qualification_id", title: "Sectors this degree leads to", summary: ["sector_id", "reason"],
        fields: [
          { name: "sector_id", label: "Sector", type: "ref", ref: "sectors", refLabel: "name", required: true },
          { name: "strength", label: "Strength (1 possible, 2 common, 3 direct)", type: "number", required: true },
          T("reason", "Reason", { required: true }),
          { name: "source_id", label: "Source id (from the Sources page)", type: "number", required: true },
        ] },
    ],
  },
  skills: {
    key: "skills", singular: "Skill", plural: "Skills", label: ["name"], sourced: true,
    fields: [T("name", "Skill name", { required: true }), slug, T("category", "Category", { required: true }), A("overview", "Overview", { required: true })],
  },
  resources: {
    key: "resources", singular: "Learning resource", plural: "Learning resources", label: ["title"], sourced: true,
    fields: [
      T("title", "Title", { required: true }), T("provider", "Provider", { required: true }), T("url", "Link", { required: true }),
      { name: "skill_id", label: "Skill", type: "ref", ref: "skills", refLabel: "name", required: true },
      { name: "format", label: "Format", type: "select", options: ["video", "course", "book", "article", "practice", "other"], required: true },
      { name: "level", label: "Level", type: "select", options: ["beginner", "intermediate", "advanced"], required: true },
      { name: "price_inr", label: "Price in rupees (0 if free)", type: "number", required: true },
      T("language", "Language", { required: true }),
      { name: "duration_hours", label: "Duration (hours)", type: "number" },
      { name: "certificate", label: "Certificate available", type: "bool" },
      { name: "sponsored", label: "Sponsored listing (must be disclosed)", type: "bool" },
    ],
  },
  companies: {
    key: "companies", singular: "Company", plural: "Companies", label: ["name"], sourced: true,
    fields: [
      T("name", "Company name", { required: true }), slug, A("summary", "Summary", { required: true }),
      T("cin", "CIN"), T("industry_code", "Industry code"), T("listing_status", "Listing status"), T("website", "Website"),
    ],
    linked: [
      { entity: "company_roles", fk: "company_id", title: "Roles with an official hiring page", summary: ["role_id", "careers_url"],
        fields: [
          { name: "role_id", label: "Role", type: "ref", ref: "roles", refLabel: "title", required: true },
          T("careers_url", "Official careers page link", { required: true, help: "Open it and confirm it works before saving" }),
          { name: "last_verified", label: "Link checked on", type: "date", required: true },
        ] },
    ],
  },
  roadmap_steps: {
    key: "roadmap_steps", singular: "Roadmap step", plural: "Roadmap steps", label: ["title"], sourced: true,
    fields: [
      { name: "qualification_id", label: "Degree", type: "ref", ref: "qualifications", refLabel: "degree", required: true },
      { name: "year_of_study", label: "Year of study", type: "number", required: true },
      T("title", "Title", { required: true }), A("detail", "Detail", { required: true }), { name: "position", label: "Order", type: "number" },
    ],
  },
  news: {
    key: "news", singular: "Briefing item", plural: "Briefing items", label: ["headline"], sourced: true,
    fields: [
      T("headline", "Headline", { required: true }), A("summary", "Summary", { required: true }), A("why_it_matters", "Why it matters to students", { required: true }),
      T("link", "Official link", { required: true }), { name: "event_date", label: "Event date", type: "date", required: true },
      { name: "sector_id", label: "Sector (optional)", type: "ref", ref: "sectors", refLabel: "name" },
    ],
  },
};

const PILLARS = ["foundations", "practical", "ai-era", "life-skills", "social", "elocution", "grooming", "teamwork", "growth", "executive", "entrepreneurship", "govt-exams", "digital-safety", "academic", "career", "global", "wellness"];
const QPILLARS = [...PILLARS, "interview", "case-knowledge"];
const SCEN = ["case", "jugaad", "crisis", "ethics", "leadership", "ai_vs_human", "negotiation", "thinker", "conflict"];
const sel = (name: string, label: string, options: string[], extra: Partial<Field> = {}): Field => ({ name, label, type: "select", options, ...extra });
const num = (name: string, label: string, extra: Partial<Field> = {}): Field => ({ name, label, type: "number", ...extra });
const REF_SECTOR: Field = { name: "sector_id", label: "Sector (optional)", type: "ref", ref: "sectors", refLabel: "name" };
const REF_SKILL: Field = { name: "skill_id", label: "Skill (optional)", type: "ref", ref: "skills", refLabel: "name" };

export const ENTITY_ORDER = ["roles", "sectors", "qualifications", "skills", "resources", "companies", "roadmap_steps", "news"];
Object.assign(ENTITIES, {
  lessons: { key: "lessons", singular: "Lesson", plural: "Lessons", label: ["title"], sourced: true,
    hint: "Write in your own words from the cited syllabus or standard. Never paste from a textbook. The body needs at least 100 characters to be submitted.",
    fields: [T("title", "Title", { required: true }), slug, sel("pillar", "Area", PILLARS, { required: true }), T("track", "Track (a short series name)", { required: true }), A("summary", "Summary", { required: true }), A("body", "Lesson text", { required: true }),
      sel("level", "Level", ["beginner", "intermediate", "advanced"]), num("minutes", "Minutes to read"), T("language", "Language"), REF_SKILL, num("position", "Order in track")] },
  library_items: { key: "library_items", singular: "Library item", plural: "Library items", label: ["title"], sourced: true,
    hint: "Link only. Add an item only if you can show the legal basis for reading it free, and write that basis in the licence note. Never upload a book.",
    fields: [T("title", "Title", { required: true }), slug, T("authors", "Authors"), sel("kind", "Kind", ["book", "journal", "paper", "notes", "question_paper", "study_guide", "lab_manual", "exam_material", "reference", "audiobook", "other"], { required: true }),
      T("subject", "Subject", { required: true }), T("stream", "Stream"), T("language", "Language"), T("publisher", "Publisher"), T("access_url", "Link (https://)", { required: true }),
      sel("licence_status", "Why can students read this free?", ["open_access", "public_domain", "publisher_free_access", "licensed_partner"], { required: true }), A("licence_note", "Licence note: where you saw the permission", { required: true }),
      sel("format", "Format", ["pdf", "epub", "html", "web", "audio", "video"]), T("level", "Level"), num("edition_year", "Edition year")] },
  questions: { key: "questions", singular: "Question", plural: "Questions", label: ["stem"], sourced: true,
    hint: "MCQ: give 2 to 6 options as one per line, the position of the correct one starting at 0, and an explanation. Open: give guidance on what a strong answer covers.",
    fields: [slug, sel("pillar", "Area", QPILLARS, { required: true }), T("topic", "Topic", { required: true }), sel("kind", "Kind", ["mcq", "open"], { required: true }), A("stem", "Question", { required: true }),
      { name: "options", label: "Options (one per line)", type: "lines" }, num("correct_index", "Correct option number (first is 0)"), A("explanation", "Explanation"), A("guidance", "What a strong answer covers (open questions)"),
      num("difficulty", "Difficulty 1 to 3"), REF_SKILL, REF_SECTOR, { name: "role_id", label: "Role (optional)", type: "ref", ref: "roles", refLabel: "title" }] },
  assessments: { key: "assessments", singular: "Assessment", plural: "Assessments", label: ["title"], sourced: true,
    hint: "Needs at least 3 distinct published MCQs. Internal means Samarthya's own practice. Partner or accredited needs the issuer and its official page; we never imply we issue it.",
    fields: [T("title", "Title", { required: true }), slug, sel("pillar", "Area", QPILLARS, { required: true }), A("description", "Description", { required: true }), num("duration_minutes", "Suggested minutes"),
      { name: "question_slugs", label: "Question slugs (one per line)", type: "lines" }, sel("credential_type", "Credential type", ["internal", "partner", "accredited"]), T("issuer", "Issuer (partner or accredited)"), T("official_url", "Issuer's official page (https://)")] },
  scenarios: { key: "scenarios", singular: "Scenario", plural: "Scenarios", label: ["title"], sourced: true,
    hint: "Cases and Jugaad challenges. Nodes are JSON: see content/templates/scenarios.example.json. Every end scene needs a debrief, choices need consequences, scores are whole numbers from -3 to 3, and there can be no loops.",
    fields: [T("title", "Title", { required: true }), slug, sel("pillar", "Kind", SCEN, { required: true }), A("brief", "Setting the scene", { required: true }), { name: "dimensions", label: "Dimensions scored (one per line)", type: "lines" },
      num("difficulty", "Difficulty 1 to 3"), num("minutes", "Minutes"), { name: "real_case", label: "Based on a documented real event", type: "bool" }, REF_SECTOR, { name: "nodes", label: "Scenes (JSON)", type: "json" }] },
  opportunities: { key: "opportunities", singular: "Opportunity", plural: "Opportunities", label: ["title"], sourced: true,
    hint: "Link to the organiser's own https page. Give a deadline or tick rolling. Expired items hide themselves.",
    fields: [T("title", "Title", { required: true }), slug, T("organisation", "Organisation", { required: true }),
      sel("kind", "Kind", ["internship", "virtual_internship", "scholarship", "fellowship", "competition", "hackathon", "workshop", "conference", "volunteering", "apprenticeship", "full_time", "part_time", "management_trainee", "graduate_programme", "research_internship", "research_assistantship", "higher_education", "entrance_exam", "entrepreneurship", "startup_programme", "innovation_challenge", "open_source", "social_impact", "government_exam", "webinar", "expert_talk", "case_competition", "showcase", "networking_event"], { required: true }),
      A("description", "About", { required: true }), A("eligibility", "Who can apply", { required: true }), T("apply_url", "Official apply link (https://)", { required: true }), { name: "deadline", label: "Deadline", type: "date" }, { name: "rolling", label: "Rolling applications", type: "bool" },
      T("location", "Location"), sel("mode", "Mode", ["remote", "onsite", "hybrid"]), T("stipend", "Stipend or value"), T("duration_text", "Duration"), num("min_year", "Earliest year of study"), num("max_year", "Latest year of study"),
      { name: "streams", label: "Streams (one per line)", type: "lines" }, { name: "skills", label: "Skill slugs (one per line)", type: "lines" }, A("selection_process", "How selection works"), REF_SECTOR] },
  global_briefs: { key: "global_briefs", singular: "Global brief", plural: "Global briefs", label: ["headline"], sourced: true,
    hint: "Neutral, sourced, step by step. 'What could happen next' lists possibilities, never predictions.",
    fields: [T("headline", "Headline", { required: true }), slug, sel("category", "Category", ["agriculture", "ai", "conflict", "defence", "diplomacy", "economics", "education", "environment", "geopolitics", "healthcare", "history", "indian_politics", "infrastructure", "international_relations", "law", "markets", "media", "science_technology", "society", "sports", "trade"], { required: true }),
      T("region", "Region"), { name: "event_date", label: "Date of the event", type: "date", required: true }, A("what_happened", "What happened", { required: true }), A("what_led", "What led to it"), A("why_matters", "Why it matters", { required: true }), A("who_affected", "Who is affected"),
      A("consequences", "Economic, political and social consequences"), A("what_next", "What could happen next (possibilities only)"), A("investigate", "What to investigate further"), { name: "connects_to", label: "Connected topics (one per line)", type: "lines" }, REF_SECTOR] },
  countries: { key: "countries", singular: "Country", plural: "Countries", label: ["name"], sourced: true,
    fields: [T("name", "Name", { required: true }), slug, T("iso_numeric", "ISO 3166 numeric code (3 digits)", { required: true, help: "Used to place it on the map, for example 356 for India" }), T("iso_alpha3", "ISO alpha-3 code"), T("region", "Region"), T("capital", "Capital"), A("summary", "Summary", { required: true }), { name: "facts", label: "Key facts (JSON object)", type: "json" }] },
  timeline_events: { key: "timeline_events", singular: "Timeline event", plural: "Timeline", label: ["title"], sourced: true,
    fields: [T("title", "Title", { required: true }), slug, num("event_year", "Year (negative for BCE)", { required: true }), A("summary", "Summary", { required: true }), T("region", "Region"), T("category", "Category"), { name: "country_id", label: "Country (optional)", type: "ref", ref: "countries", refLabel: "name" }] },
  wellness_resources: { key: "wellness_resources", singular: "Wellness resource", plural: "Wellness resources", label: ["title"], sourced: true,
    hint: "Information and support, never diagnosis. Helplines need a phone number. A second person re-checks every number against the operator's official page.",
    fields: [T("title", "Title", { required: true }), slug, sel("kind", "Kind", ["helpline", "directory", "article", "exercise", "campus"], { required: true }), A("summary", "Summary", { required: true }), T("phone", "Phone"), T("url", "Official page (https://)"), T("hours", "Hours"), { name: "languages", label: "Languages (one per line)", type: "lines" }, T("cost", "Cost"), T("audience", "Who it is for"), T("region", "Region")] },
  practical_tools: { key: "practical_tools", singular: "Practical tool", plural: "Practical tools", label: ["name"], sourced: true,
    hint: "Jugaad Lab directory. Prices change often, so check the free and paid details against the official page on the day you review it.",
    fields: [T("name", "Name", { required: true }), slug, sel("category", "Category", ["design", "office", "coding", "data", "ai", "productivity", "research", "automation", "pdf-and-files"], { required: true }), A("what_for", "What it is good for", { required: true }), T("free_option", "What the free plan offers"), T("paid_details", "Paid plans (summary)"), T("url", "Official site (https://)", { required: true }), T("learn_url", "Official learning page (https://)")] },
} as Record<string, EntityConfig>);
ENTITY_ORDER.push("lessons", "library_items", "questions", "assessments", "scenarios", "opportunities", "global_briefs", "countries", "timeline_events", "wellness_resources", "practical_tools");
export const STATUS_LABEL: Record<string, string> = { draft: "Draft", in_review: "In review", published: "Published" };
export const labelOf = (cfg: EntityConfig, row: Record<string, unknown>) =>
  cfg.label.map((k) => row[k]).filter(Boolean).join(", ") || `#${row.id}`;

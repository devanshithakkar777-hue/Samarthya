export type Dest = { key: string; name: string; tagline: string; href: string };
/** The seven destinations. Careers, companies and the rest sit inside them. */
export const DEST: Dest[] = [
  { key: "learn", name: "Learn", tagline: "Knowledge, skills and study tools", href: "/learn" },
  { key: "explore", name: "Explore", tagline: "Careers, companies, opportunities and the world", href: "/explore" },
  { key: "practise", name: "Practise", tagline: "Questions, cases, simulations and assessments", href: "/practise" },
  { key: "grow", name: "Grow", tagline: "Workplace growth, leadership and your own ventures", href: "/grow" },
  { key: "live", name: "Live", tagline: "Money, life skills, presence and wellbeing", href: "/live" },
  { key: "connect", name: "Connect", tagline: "Community, mentors, teams and your institution", href: "/connect" },
  { key: "journey", name: "My journey", tagline: "Your profile, resumes, goals, evidence and progress", href: "/journey" },
];
export type Pillar = { number: number; name: string; destination: string; path: string; published_items: number | null };

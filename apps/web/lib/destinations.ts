export type Destination = {
  key: string; name: string; short: string; contains: string; now: string; later: string;
  state: "open" | "partial" | "later"; href?: string;
};

// Seven destinations, all built. Content in each is draft until a named reviewer approves it,
// so the labels below say what is built, never that the content is verified.
export const DESTINATIONS: Destination[] = [
  { key: "learn", name: "Learn", short: "Knowledge and skills", state: "open", href: "/learn",
    contains: "Academy lessons, link-only library, skills, study tools, personalised recommendations, progress.",
    now: "Academy, library, skills, study planner and progress are built. Items appear as they are sourced and reviewed.", later: "More lessons and library items as reviewers approve them." },
  { key: "explore", name: "Explore", short: "Careers, opportunities, the world", state: "open", href: "/explore",
    contains: "Career intelligence, opportunities and tracker, world briefs and country guides.",
    now: "Careers, opportunities with an application tracker, and world briefs are built, each with its source.", later: "A fuller opportunity timeline as content is reviewed." },
  { key: "practise", name: "Practise", short: "Rehearse the real thing", state: "open", href: "/practise",
    contains: "Drills, open practice, case studies, scenarios, assessments.",
    now: "Drills, cases, scenarios and assessments are built. Results are private to you.", later: "More scenarios and cases once reviewed." },
  { key: "grow", name: "Grow", short: "Work, leadership, ventures", state: "open", href: "/grow",
    contains: "Career growth log, 30-60-90 day plan, promotion readiness, salary and offer tools, career switching, venture tracker.",
    now: "Growth log, plans, offer calculators, career-switch tool and venture tracker are built. Pay figures are never invented.", later: "Executive and founder lessons once practitioners review them." },
  { key: "live", name: "Live", short: "Life skills and wellbeing", state: "open", href: "/live",
    contains: "Money and life calculators, wellness resources, private encrypted journal.",
    now: "Calculators, crisis resources and a private journal are built. Wellness data stays isolated.", later: "More resources once reviewed." },
  { key: "connect", name: "Connect", short: "People and institutions", state: "open", href: "/connect",
    contains: "Moderated community, approved mentors, group sessions, teams, institution partnerships.",
    now: "Moderated boards, mentor requests and institution tools are built. Mentors need reviewer approval.", later: "Real mentors and institutions join after review." },
  { key: "journey", name: "My journey", short: "Profile, goals, progress", state: "open", href: "/journey",
    contains: "Master profile, resumes, portfolio, defence practice, credentials, roadmap, progress and your AI companion.",
    now: "Everything here is private to you. Progress is personal, with no streaks and no leaderboards.", later: "A fuller development timeline as it grows." },
];

export const STAGES = ["Discover", "Learn", "Explore", "Practise", "Develop", "Lead", "Contribute"];
export const ENVIRONMENTS = ["Education", "Knowledge", "Skills", "Career guidance", "Practical experience", "Mentorship", "Opportunities"];

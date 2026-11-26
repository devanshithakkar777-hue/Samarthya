"""Shared vocabulary: pillars, allowed values and the map from the 22 blueprint pillars to what is built."""

# Lesson / question pillars. Tracks inside a pillar are free text so editors can add topics.
PILLARS = {
    "foundations": "Foundations (English, maths, reasoning, critical thinking, information literacy)",
    "practical": "Practical intelligence and the Jugaad Lab",
    "ai-era": "AI-era employability and human + AI skills",
    "life-skills": "Life skills and adulting",
    "social": "Communication, teamwork and leadership",
    "elocution": "Speaking, elocution and confidence",
    "grooming": "Grooming and professional presence",
    "teamwork": "Teamwork and project management",
    "growth": "Growth after you are hired",
    "executive": "Executive and strategic leadership",
    "entrepreneurship": "Entrepreneurship and independent work",
    "govt-exams": "Government and competitive exams",
    "digital-safety": "Digital safety, privacy and scam awareness",
    "academic": "Study skills and academic development",
    "career": "Career, resume and interview",
    "global": "Global intelligence and awareness",
    "wellness": "Wellbeing education",
}
QUESTION_PILLARS = set(PILLARS) | {"interview", "case-knowledge"}
SCENARIO_PILLARS = {"case": "Real-world case", "jugaad": "Jugaad challenge", "crisis": "Crisis management",
                    "ethics": "Ethical dilemma", "leadership": "Leadership and teams",
                    "ai_vs_human": "AI versus human", "negotiation": "Negotiation",
                    "thinker": "Global Thinker Challenge", "conflict": "Team conflict simulator"}
LEVELS = {"beginner", "intermediate", "advanced"}
LIBRARY_KINDS = {"book", "paper", "journal", "notes", "study_guide", "lab_manual", "question_paper", "exam_material",
                 "reference", "audiobook", "other"}
# Only these let an item be published. "unverified" never appears: an item with no clear right to link is not listed.
LICENCE_STATUS = {"open_access": "Open access", "public_domain": "Public domain",
                  "publisher_free_access": "Free access granted by the publisher or institution",
                  "licensed_partner": "Licensed through a partnership"}
LIBRARY_FORMATS = {"pdf", "html", "epub", "audio", "web", "video"}
OPPORTUNITY_KINDS = {"internship", "full_time", "part_time", "apprenticeship", "graduate_programme", "management_trainee",
                     "research_internship", "research_assistantship", "fellowship", "scholarship", "competition",
                     "hackathon", "innovation_challenge", "startup_programme", "volunteering", "social_impact",
                     "entrepreneurship", "conference", "workshop", "virtual_internship", "open_source",
                     "higher_education", "entrance_exam", "government_exam", "webinar", "expert_talk",
                     "case_competition", "showcase", "networking_event"}
OPPORTUNITY_MODES = {"remote", "onsite", "hybrid"}
BRIEF_CATEGORIES = {"geopolitics", "international_relations", "conflict", "diplomacy", "indian_politics", "economics",
                    "trade", "markets", "environment", "science_technology", "ai", "healthcare", "society", "history",
                    "law", "defence", "agriculture", "infrastructure", "education", "media", "sports"}
TOOL_CATEGORIES = {"design", "office", "coding", "data", "ai", "productivity", "research", "automation", "pdf-and-files"}
WELLNESS_KINDS = {"helpline", "directory", "article", "exercise", "campus"}
CREDENTIAL_TYPES = {"internal", "partner", "accredited"}
RESUME_TARGETS = {"general", "sector", "role", "company", "job_description", "internship", "research", "academic_cv",
                  "fresher", "experienced"}
MASTER_SECTIONS = ["education", "skill", "project", "internship", "experience", "certification", "achievement",
                   "competition", "leadership", "volunteering", "publication", "extracurricular", "language",
                   "workplace_win", "feedback_received", "responsibility", "promotion", "workplace_learning",
                   "plan_30_60_90", "kpi_okr", "promotion_check", "six_month_review", "leadership_log"]
EVIDENCE_KINDS = {"github", "portfolio", "certificate", "publication", "presentation", "other"}
APPLICATION_STATUS = ["saved", "preparing", "applied", "interview", "offer", "rejected", "withdrawn"]
STUDY_KINDS = {"revision", "assignment", "exam", "practical", "backlog", "reading", "goal"}
BOARDS = {
    "study-groups": "Study groups and academic help",
    "careers": "Careers and industries",
    "projects": "Projects and teammates",
    "debate": "Debate arena: current affairs, ethics, technology, policy",
    "skills-exchange": "Skill exchange and peer teaching",
    "campus-life": "Campus life and adjusting",
    "regional": "Regional and language groups",
}
MENTOR_KINDS = {"industry", "alumni", "academic", "research", "entrepreneurship"}

# field -> allowed values, checked when editors save content
CHOICES: dict[str, dict[str, set]] = {
    "lessons": {"pillar": set(PILLARS), "level": LEVELS},
    "library_items": {"kind": LIBRARY_KINDS, "licence_status": set(LICENCE_STATUS), "format": LIBRARY_FORMATS},
    "questions": {"pillar": QUESTION_PILLARS, "kind": {"mcq", "open"}},
    "assessments": {"pillar": QUESTION_PILLARS, "credential_type": CREDENTIAL_TYPES},
    "scenarios": {"pillar": set(SCENARIO_PILLARS)},
    "opportunities": {"kind": OPPORTUNITY_KINDS, "mode": OPPORTUNITY_MODES},
    "global_briefs": {"category": BRIEF_CATEGORIES},
    "wellness_resources": {"kind": WELLNESS_KINDS},
    "practical_tools": {"category": TOOL_CATEGORIES},
}

# The 22 pillars in the product blueprint, where they live, and how far each is built.
# status: "built" = the tools work end to end; content is still being written and reviewed by people.
DESTINATIONS = ["learn", "explore", "practise", "grow", "live", "connect", "journey"]
BLUEPRINT = [
    (1, "Academic Intelligence and Digital E-Library", "learn", "/library"),
    (2, "Foundational Intelligence Academy", "learn", "/academy"),
    (3, "Practical Intelligence and the Jugaad Lab", "practise", "/practise"),
    (4, "Career Intelligence and Industry Discovery", "explore", "/explore"),
    (5, "Company Intelligence Database", "explore", "/companies"),
    (6, "Skill Development and Learning Resources", "learn", "/skills"),
    (7, "Resume Intelligence and Personal Branding", "journey", "/build/resumes"),
    (8, "Resume Defence and Interview Intelligence", "journey", "/build/defence"),
    (9, "Real-World Case and Situational Readiness", "practise", "/practise/cases"),
    (10, "Global Intelligence and Awareness", "explore", "/world"),
    (11, "AI-Era Employability and Human + AI Intelligence", "learn", "/academy?pillar=ai-era"),
    (12, "Life Skills and Adulting Academy", "live", "/live"),
    (13, "Student Wellness and Mental Wellbeing", "live", "/live/wellness"),
    (14, "Social, Interpersonal and Leadership Development", "live", "/academy?pillar=social"),
    (15, "Career Opportunities and Experience Marketplace", "explore", "/opportunities"),
    (16, "Community, Mentorship and Collaboration", "connect", "/connect"),
    (17, "Unified Student Intelligence Profile", "journey", "/build"),
    (18, "Personalised AI Companion", "journey", "/companion"),
    (19, "Personalised Learning and Development Engine", "journey", "/for-you"),
    (20, "Gamification and Motivation System", "journey", "/progress"),
    (21, "Assessment and Certification Ecosystem", "practise", "/practise/assessments"),
    (22, "Institution and University Ecosystem", "connect", "/institution"),
    (23, "Teamwork, Collaboration and Leadership Academy", "connect", "/academy?pillar=teamwork"),
    (24, "Personal Grooming and Professional Presence", "live", "/academy?pillar=grooming"),
    (25, "Communication, Elocution and Confidence Academy", "live", "/learn/speaking"),
    (26, "Career Growth and Workplace Excellence", "grow", "/build/growth"),
    (27, "Entrepreneurship, Venture and Independent Work", "grow", "/build/venture"),
]

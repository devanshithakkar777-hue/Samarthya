# Samarthya: build status and review handover

Status: **feature-complete build; all content is unreviewed draft.** Nothing has been published or approved.
Reviewers: Project Founder (Primary Reviewer), Independent Reviewer (faculty mentor), plus professionals and a lawyer you bring in.
No external resource was provisioned and no credential was created. The AI companion is off until you add your own key.

## What is built (22 pillars, six destinations)

| # | Pillar | Destination | Where | Built |
|---|---|---|---|---|
| 1 | Academic Intelligence and E-Library | Learn | `/library` | Link-only library with licence basis per item; no copies hosted |
| 2 | Foundational Intelligence Academy | Learn | `/academy` | Lessons, per-learner progress |
| 3 | Practical Intelligence / Jugaad Lab | Practise | `/practise`, `/practise/open` | Drills and open-ended practice |
| 4 | Career Intelligence | Explore | `/explore` | Sectors, roles, pathways |
| 5 | Company Intelligence | Explore | `/companies` | Company pages with sources |
| 6 | Skills and Learning Resources | Learn | `/skills` | Skill pages and resources |
| 7 | Resume and Personal Branding | Build | `/build/resumes`, `/build/portfolio` | Versions, check, DOCX/PDF export, opt-in public portfolio |
| 8 | Resume Defence / Interview | Build | `/build/defence` | Question bank, answers, readiness |
| 9 | Cases and Situational Readiness | Practise | `/practise/cases` | Cases and scenarios |
| 10 | Global Intelligence | Explore | `/world` | Briefs, country guides, server-rendered map |
| 11 | AI-Era Employability | Learn | `/academy?pillar=ai-era` | Lesson pillar filter |
| 12 | Life Skills | Live | `/live` | Calculators |
| 13 | Wellness | Live | `/live/wellness` | Crisis box, resources, encrypted journal (no diagnosis) |
| 14 | Social and Leadership | Learn | `/academy?pillar=social` | Lesson pillar filter |
| 15 | Opportunities Marketplace | Explore | `/opportunities`, `/applications` | Listings, match, tracker, reminders, .ics |
| 16 | Community and Mentorship | Connect | `/connect` | Moderated boards, reports, mentor requests |
| 17 | Unified Student Profile | Build | `/build` | Master profile feeding resumes and portfolio |
| 18 | AI Companion | Build | `/companion` | Rule-based by default; optional LLM behind guardrails |
| 19 | Personalised Learning Engine | Learn | `/for-you`, `/study` | Recommendations, planner, decks |
| 20 | Gamification | Practise | `/progress` | Private streaks and internal badges; no public leaderboards |
| 21 | Assessment and Certification | Practise | `/practise/assessments` | Assessments; badges are internal, not accredited credentials |
| 22 | Institution Ecosystem | Connect | `/institution` | Join code, consent, aggregate overview only |

### Added in the latest round
Scam checker (`/live/scam-check`, rule-based, never says an offer is genuine), interest explorer (`/explore/discover`), daily briefing (`/world/daily`), events page (`/connect/events`), citation helper (`/learn/cite`), speaking practice (`/learn/speaking`, browser speech recognition, disclosed), growth log (`/build/growth`), opt-in read-only parent link (`/parent/<token>`, revocable, no-store, token redacted in logs), extra institution aggregates (k>=10 rule kept), new pillars and opportunity kinds, library multi-word search.

### Added in the second round (all covered by tests)
Library notes and highlights (`/learn/notes`, the student types their own; no book text is stored), concept maps (`/learn/concept-maps`), study assistant (`/learn/study-assistant`, sourced pages plus the student's own notes; AI when a key is set), mock interviewer (`/practise/mock-interview`, typed or browser-dictated, rule-based feedback or AI), group mentoring sessions (`/connect/sessions`, mentor adds own meeting link), mentor dashboard, employer dashboard (employers submit drafts only; counts hidden under 10), entrepreneur venture tracker (`/build/venture`), company prep packs (`/companies/<slug>/prep`, filled by lessons/questions whose track or topic is `prep-<company-slug>`), career-switch roadmap (`/explore/career-switch`), partner-issued credentials (admin records them; public verify endpoint shows no holder details). The AI companion now supports Anthropic, Gemini, Groq and OpenRouter through `LLM_PROVIDER`.

Not built with a screen yet: admin screens for creating employers and recording partner credentials (use the API: `POST /v1/org-admin/employers`, `POST /v1/org-admin/credentials`). The study assistant cannot search inside book text, because the library is link-only by design.

### Draft content ready to import
`content/imports/`: `wellness_resources.csv` (6 helplines), `library_items.csv` (9 open or free-access libraries), `opportunities.csv` (5: PM Internship Scheme, National Scholarship Portal, UPSC CSE, SSC CGL, GATE), `lessons.csv` (2 digital-safety lessons). Each row has a source URL and last-verified date 2026-11-26. All import as drafts only; nothing is published. Opportunity rows carry no deadlines on purpose: add them from each year's official notice. Verify helpline numbers and timings, especially iCALL hours, before approving.

Checks run at handover: 177 API tests pass; Next.js build and typecheck pass (no API needed at build time); all key pages return 200 against a live API; the faculty mentor's name appears nowhere in the repo.

## Honest gaps (these are not bugs; they need people)

1. **Content is empty or draft.** Lessons, library items, questions, cases, scenarios, opportunities, briefs, countries and wellness resources must be authored (CSV/JSON templates in `content/templates`, guide in `content/EDITOR_GUIDE.md`), then approved by someone who did not write them.
2. **AI companion untested with a real model.** Needs your own key; guardrails are tested only against the rule-based path.
3. **Built but needs people:** the employer, mentor and group-session tools are software only; there are no real employers or mentors yet. The mock interviewer's video is not recorded (voice is browser dictation only). Prep packs are empty until editors write them. In-book search is not possible while the library is link-only.
3b. **PDF export cannot render Indic scripts** without a bundled Noto font. DOCX export works.
4. **Rate limiter and companion daily counter are per process.** Move to Redis before running more than one API instance.
5. **Not verified on live Render/Neon.** `TRUSTED_PROXY_HOPS` and the free-tier limits need checking on the day.
6. **No real mentors or institutions exist yet.** Mentors need approval by a reviewer who is not the mentor.
7. **Accessibility (axe) and low-data budget scripts** exist in CI but were not re-run on the new pages in this environment. Run `scripts/a11y_check.py` and `scripts/budget_check.py` before launch, plus a manual screen-reader and mobile pass.
8. **Email-code sign-in only.** Phone OTP is deferred.

## Review checklist

**Faculty mentors / professionals**
- Spot-check every sourced fact against its source and set the last-verified date.
- Re-check the crisis numbers on `/live/wellness` (Tele-MANAS, KIRAN, iCall, 112) against official sites; they were last checked 2026-11-26 and must be re-confirmed by a human.
- Review companion guardrails (no diagnosis, no medical/legal/financial advice, crisis hand-off) and the refusal text.
- Review journal and wellness copy for tone; confirm nothing implies therapy.
- Review mentor approval criteria and community house rules.

**Lawyer**
- Privacy policy and consent text against the DPDP Act 2023 and its rules: parental/guardian consent for under-18s, data principal rights, breach process, retention, deletion.
- Journal encryption and `JOURNAL_KEY` custody; what happens on key loss.
- Library licence basis per item (link-only; confirm no infringement).
- Terms of use, community rules, liability around mentor contact, and the institution data-sharing consent (aggregates only, k >= 10, off by default).
- Wording of badges so they are not mistaken for accredited certificates.
- Portfolio publishing (opt-in, indexable flag) and takedown process.

## Before launch
- Set `JOURNAL_KEY` (generated by Render) and back it up off Render.
- Create first admin, a separate editor, and the two reviewers (see DEPLOY.md section 5).
- Load content as drafts, review, publish. Export a database dump and restore it once.

## Added after the blueprint PDF was read (this round)
- **Seven destinations** now match the blueprint: Learn, Explore, Practise, Grow, Live, Connect, My journey. New pages `/grow` and `/journey`; `/build` redirects to `/journey`; the old build tools keep their URLs.
- **Blueprint pillars 23-27** (teamwork, grooming, elocution, career growth, entrepreneurship) now appear on their destination pages with honest published counts.
- **CTC to in-hand calculator and two-offer comparison** (`/v1/calc/ctc`, `/v1/calc/offers`), on Live and Grow. Income tax is typed by the user, never estimated. Not tax or legal advice.
- **Growth plan sections** in the private growth log: 30-60-90 plan, KPIs and OKRs, promotion readiness check, six-month review, leadership log.
- **Support directory**: anti-ragging helpline, SHe-Box, NALSA 15100, National Consumer Helpline, Women Helpline 181 added to `wellness_resources.csv` as drafts with official sources.
- **Interface sounds**: short tones made in the browser (no audio files). They play only when something is pressed, never on their own, and a "Sound on/off" switch sits in the header (remembered per browser).

## Built in the final round
- **Resume gap analysis** against a pasted job description or a chosen role: demonstrated / have / claimed only / out of date (4+ years) / to acquire, with links to matching skill pages. Never says you are or are not qualified.
- **Resume defence**: five difficulty levels, study / practice / simulation modes, six qualitative checks (clarity, depth, relevance, practical application, authenticity, structure, shown or not yet shown, no numbers) and an adaptive follow-up question.
- **Learning plan and capability profile** (`/learn/plan`): per-area bands from your own practice, weak topics with lesson suggestions, areas not started. No overall score.
- **Promotion readiness record** on the growth page: an eight-item checklist and entries-per-month chart. Private; predicts nothing.
- **Connect the dots** (`/world/map`): published briefs joined only where editors gave them a shared category or topic.
- **Team strengths map** (`/connect/team-strengths`): runs in the browser, nothing saved or sent.

## Still not built (from the blueprint), in plain words
1. Company-specific resume sets (one resume per target company is possible today by hand).
2. Debate arena and Global Thinker Challenge; a history explorer.
3. AI-era capability map for named roles.
4. Jugaad Lab practical tools directory (needs sourced tool data).
5. Peer feedback and retrospectives, build-your-own-team marketplace, conflict simulator beyond the existing scenarios.
6. Grooming outfit guide and occasion checklists; elocution six-step programme and simulators (recording coach needs legal review).
7. Salary intelligence and career relevance radar (need sourced, sampled data).
8. "Which government exam fits me" guide; scholarship and loan finder; study-abroad shortlisting.
9. The interactive 3D ecosystem and journey scenes (need a creative developer and real-phone tests; plain fallback is built).
10. Human-only: reviews, real content, real mentors and institutions, deployment, legal review.

## Built in the closing round
- Practical tools directory (`/practise/tools`, 8 draft entries, official pricing pages only), pay ranges (k>=10) and pay-report form, peer feedback requests (anonymous, shown at 3+ replies), company-specific resume copy, role radar.
- Presence checklists, exam guide, history explorer (`/world/timeline`), Global Thinker Challenge and Team conflict simulator scenario types.
- Speaking programme: six steps plus four unrecorded simulators (`/learn/elocution`); AI-era capability map (`/learn/ai-era`); study-abroad cost planner (`/explore/study-abroad`).
- Verification: 188 API tests pass, pyflakes clean, tsc clean, `next build` compiles.

## Still not built (needs people, sourced data or specialists)
- Interactive 3D ecosystem/journey scenes (plain fallback exists; needs a creative developer and real-phone testing).
- Scholarship/loan finder and study-abroad university shortlisting (needs sourced, dated data).
- Authored conflict/thinker scenario content, grooming outfit guide, named-role AI-era map (content to be written and reviewed as drafts).
- Human-only: faculty, professional and legal review; real mentors and institutions; deployment, Redis, Noto font for Indic PDFs; rotate the Gemini key; choose a no-training LLM provider before real student data.

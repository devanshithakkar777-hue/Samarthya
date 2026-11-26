# Samarthya content guide for editors and reviewers

Every page a student sees is something you wrote and someone else checked. These rules are what make Samarthya trustworthy.

## The five rules
1. **One source per page, and you must have opened it.** Prefer official pages (regulators, universities, government, the employer). Record the page link, title, publisher, and the date you checked it.
2. **Say only what the source says.** If you cannot find it, leave it out. An empty section is better than a guess.
3. **Plain and short.** Write for a first-year student. No jargon, no hype, no promises about jobs or salaries.
4. **Label how strong the evidence is** for every requirement:
   - `mandatory`: required by law, regulation or the employer's own posted criteria
   - `common_preference`: commonly listed in real postings, not always required
   - `recommended`: your advice, clearly useful
   - `differentiator`: not expected, but makes a student stand out
5. **Hiring pages are links, not promises.** Add an employer only with its official careers page, after opening it and confirming it works today.

## Working order (parents before children)
Sources, then sectors, degrees and skills, then roles, then requirements, then employers, resources and roadmap steps.

## How to work
- **Workspace:** sign in with your editor email, open the Workspace link in the header, choose a content type, write a draft, attach the source, and press "Send for review".
- **Bulk:** fill the CSV templates in `content/templates/` and run `python -m app.cli import <entity> <file.csv> --as you@example.org`. Rows arrive as drafts; nothing goes live until reviewed.
- **Role profile checklist (aim for 20 to 30 minutes each):** title and plain description; level; at least one requirement, each tiered; the degrees that lead here; one source; the date you checked.

## Reviewers
You cannot approve your own work. Before approving, open the source and confirm: the description matches it, each requirement's tier is justified, every link opens, copy is plain and neutral, and nothing is promised. If anything is off, "Send back with a note" and say exactly what to change.

## Keeping it fresh
The workspace home lists items not re-checked in about six months, and student reports. Re-check the source, fix anything that changed, then press "I re-checked this today".

## Learning, practice, opportunity and wellness content
These types follow the same five rules. Extra rules for each:

| Type | Extra rules before you press "Send for review" |
|---|---|
| **Lessons** | Body of at least 100 characters in your own words. Cite the syllabus or standard it follows. No copied textbook passages. |
| **Library items** | Link only, never upload a book. The link must be `https://`, and you must record the **licence basis** (`open_access`, `public_domain`, `publisher_free_access`, `licensed_partner`) and a note saying where you saw it. If you cannot show the basis, do not add the item. |
| **Questions** | MCQ: at least two options, a correct answer, and an explanation. Open questions: write guidance for what a good answer covers. Difficulty 1 to 3. |
| **Assessments** | Needs at least 3 distinct published MCQ questions. `internal` results are labelled as Samarthya's own practice. Anything `partner` or `accredited` needs the issuer and the issuer's official page, and we never imply Samarthya issues it. |
| **Scenarios** | Import as `.json` (see `templates/scenarios.example.json`). Every end scene needs a debrief, every choice a consequence, scores whole numbers from -3 to 3, no loops. Base real cases on a cited public source. |
| **Opportunities** | The apply link must be the organisation's own `https://` page. Give a deadline or mark it `rolling`. Expired items hide themselves. |
| **Global briefs, countries, timeline** | Facts and dates must come from the cited source. Write "what could happen next" as possibilities, never predictions. Keep tone neutral on contested politics. |
| **Wellness resources** | Helplines need a phone number and the operating organisation's page. The always-visible crisis list lives in `app/services/safety.py`; a reviewer re-checks every number against its official page before launch. Nothing here diagnoses or treats. |

Bulk import accepts `.csv` or `.json`. In a CSV cell, list fields can be written `a;b;c`, and structured fields as JSON text.

**Reviewers:** these items are written by people and approved by a different person. Please keep the content in draft until you have personally opened each cited source.


## Company prep packs
A prep pack is built from published lessons whose `track` is `prep-<company-slug>` and published questions whose `topic` is `prep-<company-slug>`. Source every item from the company's own careers or official pages. Do not add leaked or unofficial interview questions.

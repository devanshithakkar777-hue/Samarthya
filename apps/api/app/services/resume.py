"""Resume assembly, checks, export and defence questions.

Everything here works only from what the student typed into their master profile. Nothing is invented:
the checks point at gaps and the questions point at claims the student must be ready to explain.
"""
import io
import re
from collections import Counter

from .ask import tokens

SECTION_LABEL = {
    "education": "Education", "skill": "Skills", "project": "Projects", "internship": "Internships",
    "experience": "Work experience", "certification": "Certifications", "achievement": "Achievements",
    "competition": "Competitions", "leadership": "Leadership", "volunteering": "Volunteering",
    "publication": "Publications", "extracurricular": "Extracurricular activities", "language": "Languages",
    "workplace_win": "Work achievements", "feedback_received": "Feedback received", "responsibility": "Responsibilities",
    "promotion": "Promotions and raises", "workplace_learning": "Workplace learning",
    "plan_30_60_90": "30-60-90 day plan", "kpi_okr": "KPIs and OKRs", "promotion_check": "Promotion readiness check",
    "six_month_review": "Six-month review", "leadership_log": "Leadership log",
}
DEFAULT_ORDER = ["education", "experience", "internship", "project", "skill", "certification", "achievement",
                 "competition", "leadership", "volunteering", "publication", "extracurricular", "language"]
ACADEMIC_ORDER = ["education", "publication", "experience", "project", "competition", "achievement", "skill",
                  "certification", "leadership", "volunteering", "language"]
VERBS = set("""achieved analysed analyzed built created designed developed delivered led managed organised organized
planned launched improved increased reduced implemented wrote presented taught trained coordinated automated
tested debugged deployed researched published won secured negotiated mentored established streamlined resolved
conducted prepared produced supported maintained introduced raised collected surveyed compared evaluated""".split())
NUMBER = re.compile(r"(\d[\d,.]*\s?(%|x|k|lakh|crore|users|people|members|students|hours|days|₹|rs)?|₹\s?\d)", re.I)


def _fmt_dates(e: dict) -> str:
    def f(d):
        return d.strftime("%b %Y") if d else ""
    a, b = f(e.get("start_date")), "Present" if e.get("current") else f(e.get("end_date"))
    return f"{a} – {b}".strip(" –") if (a or b) else ""


def entry_dict(e) -> dict:
    return {"id": e.id, "section": e.section, "title": e.title, "organisation": e.organisation, "location": e.location,
            "start_date": e.start_date, "end_date": e.end_date, "current": e.current, "detail": e.detail,
            "bullets": list(e.bullets or []), "evidence": list(e.evidence or []), "tags": list(e.tags or []),
            "position": e.position}


def assemble(resume, entries: list) -> dict:
    """The resume as it will be printed: chosen entries and chosen bullets, in section order."""
    by_id = {e.id: entry_dict(e) for e in entries}
    chosen = resume.selection or [{"entry_id": i, "bullets": None} for i in by_id]
    sections: dict[str, list] = {}
    for sel in chosen:
        e = by_id.get(sel.get("entry_id"))
        if e is None:
            continue
        idx = sel.get("bullets")
        bullets = e["bullets"] if idx is None else [e["bullets"][i] for i in idx if 0 <= i < len(e["bullets"])]
        sections.setdefault(e["section"], []).append({**e, "bullets": bullets, "dates": _fmt_dates(e)})
    order = [s for s in (resume.section_order or (ACADEMIC_ORDER if resume.target_kind in ("research", "academic_cv")
                                                  else DEFAULT_ORDER)) if s in sections]
    order += [s for s in sections if s not in order]
    return {"name": (resume.contact or {}).get("name") or resume.name, "contact": resume.contact or {},
            "headline": resume.headline, "summary": resume.summary,
            "sections": [{"key": s, "label": SECTION_LABEL.get(s, s.title()),
                          "items": sorted(sections[s], key=lambda x: (x["position"], x["id"]))} for s in order]}


def _all_text(doc: dict) -> str:
    parts = [doc.get("headline") or "", doc.get("summary") or ""]
    for s in doc["sections"]:
        for it in s["items"]:
            parts += [it["title"], it.get("organisation") or "", it.get("detail") or "", *it["bullets"], *it.get("tags", [])]
    return "\n".join(parts)


def demonstrated(entries: list) -> dict[int, bool]:
    """Skill entries that are backed by evidence or appear in a project, internship or job entry."""
    body = " ".join(" ".join([e.title, *(e.bullets or []), *(e.tags or [])]).lower() for e in entries
                    if e.section in ("project", "internship", "experience", "competition", "publication"))
    out = {}
    for e in entries:
        if e.section == "skill":
            out[e.id] = bool(e.evidence) or (e.title.lower() in body)
    return out


def check(doc: dict, entries: list, jd_text: str | None = None, role_terms: list[str] | None = None) -> dict:
    findings: list[dict] = []

    def add(sev, area, msg):
        findings.append({"severity": sev, "area": area, "message": msg})

    contact = doc["contact"]
    if not (contact.get("email") or contact.get("phone")):
        add("warn", "contact", "Add an email address or phone number so employers can reach you.")
    if not doc["sections"]:
        add("warn", "content", "This resume has no entries yet. Add entries to your master profile and choose them here.")
    text = _all_text(doc)
    words = len(re.findall(r"\w+", text))
    pages = max(1, round(words / 450 + 0.49))
    senior = any(s["key"] in ("experience",) and len(s["items"]) >= 3 for s in doc["sections"])
    if pages > 1 and not senior:
        add("info", "length", f"About {words} words, roughly {pages} pages. For a fresher or student, one page is the usual expectation.")
    bullets = [(it, b) for s in doc["sections"] for it in s["items"] for b in it["bullets"]]
    if bullets:
        starts = sum(1 for _, b in bullets if b.split(" ", 1)[0].lower().strip(",.") in VERBS)
        quant = sum(1 for _, b in bullets if NUMBER.search(b))
        if starts / len(bullets) < 0.6:
            add("info", "wording", "Many bullets do not start with an action verb (built, analysed, led...). Starting with what you did reads more clearly.")
        if quant / len(bullets) < 0.25:
            add("info", "evidence", "Few bullets have a number. Add a real figure where you have one (people, hours, percentage). Never add a figure you cannot support.")
        for it, b in bullets:
            if len(b.split()) > 35:
                add("info", "wording", f"A bullet under '{it['title']}' is long ({len(b.split())} words). Shorter is easier to read and to defend.")
                break
        if any(re.search(r"\b(i|my|me)\b", b, re.I) for _, b in bullets):
            add("info", "wording", "Some bullets use I/my/me. Resume bullets usually leave these out.")
    for s in doc["sections"]:
        for it in s["items"]:
            if s["key"] in ("education", "internship", "experience") and not it.get("dates"):
                add("info", "dates", f"'{it['title']}' has no dates.")
            if s["key"] in ("project", "internship", "experience") and not it["bullets"]:
                add("info", "content", f"'{it['title']}' has no bullets. Say what you did and what came of it.")
    if not any(s["key"] == "education" for s in doc["sections"]):
        add("warn", "content", "No education entry is selected.")

    # self-reported versus demonstrated skills
    demo = demonstrated(entries)
    ids = {it["id"] for s in doc["sections"] for it in s["items"]}
    unsupported = [e.title for e in entries if e.section == "skill" and e.id in ids and not demo.get(e.id)]
    if unsupported:
        add("info", "evidence", "Skills listed with no project, job or evidence that shows them (self-reported): "
            + ", ".join(unsupported[:10]) + ". Be ready to show or explain each, or add a project that uses it.")

    # keyword and requirement alignment
    align = {"matched": [], "missing": [], "basis": None}
    terms: Counter = Counter()
    if jd_text and jd_text.strip():
        align["basis"] = "job description"
        for t in tokens(jd_text):
            terms[t] += 1
        wanted = [t for t, c in terms.most_common(40) if c >= 2 or len(t) > 5][:25]
    elif role_terms:
        align["basis"] = "role requirements"
        wanted = sorted({t for term in role_terms for t in tokens(term)})
    else:
        wanted = []
    have = set(tokens(text))
    for t in wanted:
        (align["matched"] if t in have else align["missing"]).append(t)
    if align["missing"]:
        add("info", "keywords", "Terms from the " + align["basis"] + " that your resume does not mention: "
            + ", ".join(align["missing"][:12]) + ". Add one only if it is true for you and you can talk about it.")
    return {"findings": findings, "stats": {"words": words, "approx_pages": pages, "bullets": len(bullets)},
            "alignment": align,
            "ats_note": "Exports use one column, plain headings and no images or tables, which is the safest layout for applicant tracking systems. No tool can promise how a particular employer's system will read it."}


def suggest_selection(entries: list, jd_text: str | None = None, role_terms: list[str] | None = None, max_per_section: int = 4) -> list[dict]:
    """Rank entries by overlap with the target. Suggestion only: the student confirms what to include."""
    target = set(tokens(jd_text or "")) | {t for term in (role_terms or []) for t in tokens(term)}
    scored = []
    for e in entries:
        words = set(tokens(" ".join([e.title, e.organisation or "", e.detail or "", *(e.bullets or []), *(e.tags or [])])))
        scored.append((len(words & target) if target else 0, e))
    out, counts = [], Counter()
    for score, e in sorted(scored, key=lambda x: (-x[0], x[1].position, x[1].id)):
        cap = 99 if e.section in ("education", "language") else max_per_section
        if counts[e.section] >= cap:
            continue
        if target and score == 0 and e.section not in ("education", "language"):
            continue
        counts[e.section] += 1
        out.append({"entry_id": e.id, "bullets": None})
    return out


# ---------------------------------------------------------------- export
def to_docx(doc: dict) -> bytes:
    from docx import Document
    from docx.shared import Pt

    d = Document()
    style = d.styles["Normal"]
    style.font.name, style.font.size = "Calibri", Pt(10.5)
    d.add_heading(doc["name"], level=0)
    contact = doc["contact"]
    line = " | ".join(str(contact[k]) for k in ("email", "phone", "location") if contact.get(k))
    links = [str(x) for x in contact.get("links", []) if x]
    if line or links:
        d.add_paragraph(" | ".join([x for x in [line, *links] if x]))
    if doc.get("headline"):
        d.add_paragraph(doc["headline"])
    if doc.get("summary"):
        d.add_heading("Summary", level=1)
        d.add_paragraph(doc["summary"])
    for s in doc["sections"]:
        d.add_heading(s["label"], level=1)
        for it in s["items"]:
            head = ", ".join(x for x in [it["title"], it.get("organisation")] if x)
            p = d.add_paragraph()
            p.add_run(head).bold = True
            meta = " | ".join(x for x in [it.get("dates"), it.get("location"), it.get("detail")] if x)
            if meta:
                p.add_run("  " + meta)
            for b in it["bullets"]:
                d.add_paragraph(b, style="List Bullet")
            for ev in it.get("evidence", []):
                if ev.get("url"):
                    d.add_paragraph(f"{ev.get('label') or ev.get('kind', 'Link')}: {ev['url']}")
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def _pdf_fonts() -> tuple[str, str, bool]:
    """DejaVu Sans if installed (covers the rupee sign and most Latin scripts), else the built-in Helvetica.
    Indic scripts need a font such as Noto Sans Devanagari; use the Word export for those names."""
    import os

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"):
        r, b = os.path.join(d, "DejaVuSans.ttf"), os.path.join(d, "DejaVuSans-Bold.ttf")
        if os.path.exists(r) and os.path.exists(b):
            for name, path in (("DejaVuSans", r), ("DejaVuSans-Bold", b)):
                if name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(name, path))
            return "DejaVuSans", "DejaVuSans-Bold", True
    return "Helvetica", "Helvetica-Bold", False


def to_pdf(doc: dict) -> bytes:
    from xml.sax.saxutils import escape

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

    regular, bold, unicode_ok = _pdf_fonts()
    base = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=base["Normal"], fontName=regular, fontSize=10, leading=13)
    h1 = ParagraphStyle("h1", parent=base["Heading2"], fontName=bold, fontSize=12, spaceBefore=8, spaceAfter=3)
    name = ParagraphStyle("n", parent=base["Title"], fontName=bold, fontSize=18, alignment=0, spaceAfter=2)
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                            title=doc["name"], author=doc["name"])
    # without a Unicode font the built-in Helvetica cannot draw the rupee sign, so it is written as "Rs."
    e = (lambda t: escape(str(t))) if unicode_ok else (lambda t: escape(str(t).replace("₹", "Rs. ")))  # noqa: E731
    flow = [Paragraph(e(doc["name"]), name)]
    contact = doc["contact"]
    bits = [str(contact[k]) for k in ("email", "phone", "location") if contact.get(k)] + [str(x) for x in contact.get("links", []) if x]
    if bits:
        flow.append(Paragraph(e(" | ".join(bits)), body))
    if doc.get("headline"):
        flow.append(Paragraph(e(doc["headline"]), body))
    if doc.get("summary"):
        flow += [Paragraph("Summary", h1), Paragraph(e(doc["summary"]), body)]
    for s in doc["sections"]:
        flow.append(Paragraph(e(s["label"]), h1))
        for it in s["items"]:
            head = ", ".join(x for x in [it["title"], it.get("organisation")] if x)
            meta = " | ".join(x for x in [it.get("dates"), it.get("location"), it.get("detail")] if x)
            flow.append(Paragraph(f"<b>{e(head)}</b>" + (f"  {e(meta)}" if meta else ""), body))
            if it["bullets"]:
                flow.append(ListFlowable([ListItem(Paragraph(e(b), body), leftIndent=10) for b in it["bullets"]],
                                         bulletType="bullet", start="•", leftIndent=12))
            for ev in it.get("evidence", []):
                if ev.get("url"):
                    flow.append(Paragraph(e(f"{ev.get('label') or ev.get('kind', 'Link')}: {ev['url']}"), body))
            flow.append(Spacer(1, 3))
    pdf.build(flow)
    return buf.getvalue()


# ---------------------------------------------------------------- defence questions
_GENERIC = {
    "project": [("walkthrough", "Walk me through {t} from the problem you were solving to the result."),
                ("contribution", "Which parts of {t} did you personally build, and which did others do?"),
                ("challenge", "What was the hardest problem in {t}, and how did you solve it?"),
                ("verification", "How did you know {t} worked? What did you test?"),
                ("hindsight", "If you rebuilt {t} today, what would you change and why?")],
    "internship": [("day", "Describe a normal day during {t}."),
                   ("delivered", "What did you deliver during {t} that someone actually used?"),
                   ("feedback", "What feedback did you get during {t}, and what did you do with it?"),
                   ("learning", "What is the most important thing {t} taught you about working in a team?")],
    "experience": [("day", "Describe a normal day in {t}."),
                   ("impact", "What changed because of your work in {t}?"),
                   ("difficulty", "Tell me about a difficult situation in {t} and what you did."),
                   ("learning", "What did you learn in {t} that you would not have learned in a classroom?")],
    "certification": [("learned", "What did you learn in {t} that you have actually used?"),
                      ("explain", "Pick one topic from {t} and explain it to me as if I had never heard of it.")],
    "achievement": [("how", "How did you achieve {t}? What did it take?"),
                    ("meaning", "Why does {t} matter, and what did you do differently from others?")],
    "competition": [("approach", "How did your team approach {t}?"),
                    ("result", "What went wrong in {t}, and how did you respond?")],
    "leadership": [("scope", "How many people did you lead in {t}, and how did you decide who did what?"),
                   ("conflict", "Tell me about a disagreement in {t} and how you handled it.")],
    "volunteering": [("why", "Why did you take up {t}, and what did you change or learn?")],
    "publication": [("question", "What question did {t} try to answer, and how did you go about it?"),
                    ("limits", "What are the limitations of {t}?")],
    "extracurricular": [("why", "What did {t} teach you that you use now?")],
    "education": [("subjects", "Which subject in {t} did you enjoy most, and what is one idea from it you can explain?"),
                  ("gap", "Where were you weakest in {t}, and what did you do about it?")],
}
_LEAD = re.compile(r"\b(led|managed|organised|organized|coordinated|headed|captain|ran)\b", re.I)


def defence_questions(entries: list, limit: int = 40) -> list[dict]:
    out: list[dict] = []
    demo = demonstrated(entries)
    for e in entries:
        t = e.title
        for topic, tmpl in _GENERIC.get(e.section, []):
            out.append({"entry_id": e.id, "topic": topic, "source_line": t, "question": tmpl.format(t=t), "kind": "entry"})
        for tag in (e.tags or [])[:4]:
            if e.section in ("project", "internship", "experience"):
                out.append({"entry_id": e.id, "topic": "technical", "source_line": f"{t}: {tag}",
                            "question": f"In {t} you used {tag}. Why that choice, and what would you have used otherwise?", "kind": "technical"})
        for b in (e.bullets or []):
            m = NUMBER.search(b)
            if m:
                out.append({"entry_id": e.id, "topic": "numbers", "source_line": b,
                            "question": f"You wrote: \"{b}\" How was the figure \"{m.group(0).strip()}\" measured, and compared with what?", "kind": "claim"})
            if _LEAD.search(b):
                out.append({"entry_id": e.id, "topic": "leadership", "source_line": b,
                            "question": f"You wrote: \"{b}\" Who exactly did you lead, and what did you do when someone did not deliver?", "kind": "claim"})
        if e.section == "skill":
            out.append({"entry_id": e.id, "topic": "skill", "source_line": t,
                        "question": f"Explain {t} to someone who has never used it. Then show me the hardest thing you have done with it.", "kind": "skill"})
            if not demo.get(e.id):
                out.append({"entry_id": e.id, "topic": "truth-audit", "source_line": t,
                            "question": f"You list {t}. Which project, job or piece of work shows it? If none does, are you comfortable keeping it on the resume?", "kind": "audit"})
    out.append({"entry_id": None, "topic": "cross-question", "source_line": "",
                "question": "Pick the claim on your resume you are least sure about. What would an interviewer ask you about it, and what is your honest answer?", "kind": "audit"})
    # keep a spread across entries instead of exhausting one project first
    seen: Counter = Counter()
    ordered = sorted(out, key=lambda q: (seen.__setitem__(q["entry_id"], seen[q["entry_id"]] + 1) or seen[q["entry_id"]]))
    for q in ordered:
        q["level"] = LEVEL_BY_KIND.get(q["kind"], 1) if q["topic"] != "cross-question" else 5
        q["hint"] = HINT_BY_KIND.get(q["kind"], "Give one real example, say what you personally did, and what came of it.")
    return ordered[:limit]


LEVELS_TEXT = {1: "Explain it", 2: "Justify the choices", 3: "Defend the numbers and claims", 4: "Prove it or drop it", 5: "Cross-question under pressure"}
LEVEL_BY_KIND = {"entry": 1, "technical": 2, "skill": 2, "claim": 3, "audit": 4}
HINT_BY_KIND = {"entry": "Say what the work was, your part in it, and one thing that went wrong or surprised you.",
                "technical": "Name the options you had, why you chose this one, and what you would change.",
                "skill": "Explain it simply first, then show the hardest real thing you did with it.",
                "claim": "Say how the figure was measured, against what, and who can confirm it.",
                "audit": "Point to the work that shows it. If there is none, say so honestly."}

DIMENSIONS = ["clarity", "depth", "relevance", "practical application", "authenticity", "structure"]


def answer_dimensions(answer: str, question: str = "") -> dict:
    """Six qualitative checks, each 'shown' or 'not yet shown'. No numbers and no total, so nobody mistakes it for a grade."""
    words = re.findall(r"\w+", answer)
    low = answer.lower()
    sentences = [x for x in re.split(r"[.!?]+", answer) if x.strip()]
    q_terms = {t for t in tokens(question) if len(t) > 4}
    shown = {
        "clarity": bool(sentences) and (len(words) / max(1, len(sentences))) <= 28 and len(words) >= 15,
        "depth": len(words) >= 60 and bool(re.search(r"\b(because|since|so that|therefore|trade-?off|instead|alternative)\b", low)),
        "relevance": (not q_terms) or len(q_terms & set(tokens(answer))) >= 1,
        "practical application": bool(re.search(r"\b(built|used|tested|deployed|measured|ran|wrote|designed|organised|organized|applied)\b", low)),
        "authenticity": bool(re.search(r"\bi\b", low)) and bool(NUMBER.search(answer) or re.search(r"\b(learned|mistake|failed|difficult|did not|didn't)\b", low)),
        "structure": sum(1 for rx in _STAR.values() if re.search(rx, low)) >= 3,
    }
    weakest = next((d for d in DIMENSIONS if not shown[d]), None)
    follow = {"clarity": "Say that again in two short sentences, as if to a friend.",
              "depth": "Why did you do it that way and not another way?",
              "relevance": "Which part of that answers the question you were asked?",
              "practical application": "What did you actually build, run or test? Walk me through one step.",
              "authenticity": "What went wrong, or what would you do differently? Give one real detail.",
              "structure": "Start again: the situation, your task, what you did, and the result."}
    return {"dimensions": {d: ("shown" if shown[d] else "not yet shown") for d in DIMENSIONS},
            "follow_up": follow.get(weakest) if weakest else "Good. Now the hard one: what is the weakest part of this answer?",
            "note": "Automatic checks of how the answer is built. They cannot judge whether it is true, and they never look at accent, pace or tone."}


_STAR = {"situation": r"\b(when|during|at the time|context|situation|background|problem)\b",
         "task": r"\b(my (role|task|job|responsibility)|i was (asked|responsible|supposed)|goal|needed to)\b",
         "action": r"\b(i (built|wrote|decided|created|organised|organized|led|tested|fixed|talked|asked|planned|analysed|analyzed|designed|chose))\b",
         "result": r"\b(result|as a result|outcome|improved|reduced|increased|achieved|learned|finished|delivered|ended up)\b"}


def answer_feedback(answer: str) -> list[dict]:
    """Automatic checks on a practice answer. They look at structure, not at whether the answer is correct."""
    words = re.findall(r"\w+", answer)
    out = []

    def add(kind, msg):
        out.append({"kind": kind, "message": msg})

    n = len(words)
    if n < 40:
        add("length", f"Short ({n} words). Interviewers usually want a fuller account with an example.")
    elif n > 320:
        add("length", f"Long ({n} words). Aim for about a minute or two of speaking: tighten to the main point and one example.")
    low = answer.lower()
    missing = [k for k, rx in _STAR.items() if not re.search(rx, low)]
    if missing:
        add("structure", "Your answer does not clearly show: " + ", ".join(missing) + ". STAR (situation, task, action, result) is a useful frame for experience questions.")
    we, i = len(re.findall(r"\bwe\b", low)), len(re.findall(r"\bi\b", low))
    if we > i * 2 and we >= 4:
        add("ownership", "You say 'we' much more than 'I'. Make clear what you personally did.")
    if not NUMBER.search(answer):
        add("specifics", "No figures or concrete specifics. Where you honestly have one, a number makes the answer easier to believe.")
    if not re.search(r"\b(learn|learned|learnt|would do differently|next time|realised|realized)\b", low):
        add("reflection", "No reflection. Saying what you learned or would change shows maturity.")
    return out


def gap_analysis(entries: list, jd_text: str | None, role_terms: list[str] | None = None, today=None) -> dict:
    """Sort what a job asks for into: demonstrated, have, claimed (self-reported), out of date, or still to acquire.
    Word-overlap based, so it points at gaps to look at; it never decides that you are or are not qualified."""
    from datetime import date as _d
    today = today or _d.today()
    if jd_text and jd_text.strip():
        basis, counts = "job description", Counter(tokens(jd_text))
        wanted = [t for t, c in counts.most_common(60) if c >= 2 or len(t) > 5][:30]
    elif role_terms:
        basis, wanted = "role requirements", sorted({t for term in role_terms for t in tokens(term)})[:30]
    else:
        return {"basis": None, "items": [], "summary": {}, "note": "Add a job description to this resume, or choose a role, to see a gap analysis."}
    proof_sections = ("project", "internship", "experience", "competition", "publication", "workplace_win")

    def words(e) -> set:
        return set(tokens(" ".join([e.title, e.organisation or "", e.detail or "", *(e.bullets or []), *(e.tags or [])])))

    items = []
    for t in wanted:
        hits = [e for e in entries if t in words(e)]
        proofs = [e for e in hits if e.section in proof_sections or (e.section == "skill" and e.evidence)]
        if proofs:
            latest = max((e.end_date or (today if e.current else None) or e.start_date for e in proofs if (e.end_date or e.current or e.start_date)), default=None)
            old = bool(latest) and (today - latest).days > 4 * 365
            state = "out_of_date" if old else "demonstrated"
            ev = [e.title for e in proofs][:3]
        elif hits:
            state = "have" if any(e.section in ("education", "certification", "language", "achievement") for e in hits) else "claimed"
            ev = [e.title for e in hits][:3]
        else:
            state, ev = "to_acquire", []
        items.append({"term": t, "state": state, "evidence": ev})
    summary = Counter(i["state"] for i in items)
    return {"basis": basis, "items": items, "summary": dict(summary),
            "meaning": {"demonstrated": "Shown in a project, job or piece of work you can point to.",
                        "have": "On your profile, for example through a degree or certificate.",
                        "claimed": "Listed, but nothing in your profile shows it yet. Add proof or be ready to explain it.",
                        "out_of_date": "Last shown more than four years ago. Refresh it or say how current it is.",
                        "to_acquire": "Not on your profile. Learn it and build something with it before claiming it."},
            "note": "Based on matching words, so read it as a prompt to look closer. It never says you are or are not qualified."}

"""Ask: answers from the published knowledge base only. No generative model is involved.

Every sentence returned is copied from a published, sourced field, and every answer carries
its citations (page, source, last-verified date). If nothing in the knowledge base covers the
question well enough, the answer is a plain refusal. This is the "AI layer in retrieval-only
mode" from the build plan; a language model can later be placed on top of the same retrieval,
but only to rephrase these passages, never to add facts, and it must pass the same eval set.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from .provenance import provenance

PUB = m.Status.published
REFUSAL = "I do not have a sourced answer to that yet."
PREDICTION = ("I can't predict outcomes, promise a job, or estimate salaries. "
              "I can show what a role asks for, which degrees lead to it, and where it is hiring, with sources.")

STOP = set("""a an the and or of to in on for with is are was were be been it its this that these those i me my we our you your
do does did can could should would will how what which who whom when where why about as at by from into than then so if
not no yes any some more most much many very just also after before during get got want need needs require requires
required requirement requirements tell show give please know like become being have has had there their them they""".split())

INTENTS = {
    "degrees": {"degree", "degrees", "study", "qualification", "qualifications", "course", "courses", "background", "stream"},
    "hiring": {"apply", "hiring", "hire", "careers", "openings", "opening", "recruit", "recruits", "work", "employer", "employers"},
    "learn": {"learn", "resource", "resources", "tutorial", "free", "course", "courses", "training"},
    "requirements": {"need", "needs", "require", "requires", "required", "requirement", "requirements", "skill", "skills",
                     "eligibility", "eligible", "qualify", "prepare", "preparation", "ready", "take"},
}
PREDICTIVE = re.compile(r"\b(will i (get|land|be hired|succeed)|guarantee|how much (will|does|do) .*(earn|pay|salary)|salary|ctc|package|"
                        r"chances? of|probability|am i good enough|predict)\b", re.I)


def stem(w: str) -> str:
    for suf in ("ing", "ers", "er", "ies", "es", "s", "ed"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(text: str) -> list[str]:
    return [stem(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


@dataclass
class Passage:
    kind: str
    title: str
    path: str
    text: str
    prov: dict
    slug: str = ""
    extra: dict = field(default_factory=dict)
    tset: set = field(default_factory=set)
    title_set: set = field(default_factory=set)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def build_passages(db: Session) -> list[Passage]:
    out: list[Passage] = []
    roles = db.scalars(select(m.Role).where(m.Role.status == PUB).options(
        selectinload(m.Role.source), selectinload(m.Role.sector), selectinload(m.Role.requirements),
        selectinload(m.Role.qualifications).selectinload(m.RoleQualification.qualification),
        selectinload(m.Role.hiring).selectinload(m.CompanyRole.company))).all()
    for r in roles:
        if r.sector.status != PUB:
            continue
        body = " ".join(x for x in (r.description, r.progression or "") if x)
        out.append(Passage("role", r.title, f"/roles/{r.slug}", body, provenance(r), r.slug,
                           {"job_family": r.job_family, "sector": r.sector.name}))
    out_by_role = {p.slug: p for p in out if p.kind == "role"}
    for r in roles:
        if r.slug not in out_by_role:
            continue
        reqs = [q for q in r.requirements]
        if reqs:
            lines = {t: [q.label for q in sorted(reqs, key=lambda x: x.position) if q.tier.value == t] for t in
                     ("mandatory", "common_preference", "recommended", "differentiator")}
            out.append(Passage("requirements", r.title, f"/roles/{r.slug}", "", provenance(r), r.slug, {"lines": lines}))
        degs = [q.qualification for q in r.qualifications if q.qualification.status == PUB]
        if degs:
            out.append(Passage("degrees", r.title, f"/roles/{r.slug}", "", provenance(r), r.slug,
                               {"degrees": [d.degree + (f", {d.specialization}" if d.specialization else "") for d in degs]}))
        links = [(cr.company, cr) for cr in r.hiring if cr.company.status == PUB]
        if links:
            out.append(Passage("hiring", r.title, f"/roles/{r.slug}", "", provenance(r), r.slug,
                               {"pages": [(c.name, cr.careers_url, cr.last_verified.isoformat()) for c, cr in links]}))
    for s in db.scalars(select(m.Sector).where(m.Sector.status == PUB).options(selectinload(m.Sector.source))):
        out.append(Passage("sector", s.name, f"/explore/{s.slug}", s.summary, provenance(s), s.slug))
    for s in db.scalars(select(m.Skill).where(m.Skill.status == PUB).options(selectinload(m.Skill.source),
                                                                            selectinload(m.Skill.resources))):
        out.append(Passage("skill", s.name, f"/skills/{s.slug}", s.overview, provenance(s), s.slug,
                           {"resources": [(x.title, x.provider, x.url, x.price_inr) for x in s.resources if x.status == PUB]}))
    for c in db.scalars(select(m.Company).where(m.Company.status == PUB).options(selectinload(m.Company.source))):
        out.append(Passage("company", c.name, f"/companies/{c.slug}", c.summary, provenance(c), c.slug))
    for n in db.scalars(select(m.NewsItem).where(m.NewsItem.status == PUB).options(selectinload(m.NewsItem.source))):
        out.append(Passage("news", n.headline, "/briefing", f"{n.summary} {n.why_it_matters}", provenance(n), str(n.id),
                           {"link": n.link}))
    for p in out:
        p.title_set = set(tokens(p.title + " " + p.extra.get("job_family", "")))
        p.tset = set(tokens(p.text)) | p.title_set
        if p.kind == "role":
            p.tset |= set(tokens(p.extra.get("sector", "")))
    return out


def _intent(qtokens: set[str]) -> str | None:
    best, n = None, 0
    for name, words in INTENTS.items():
        hit = len({stem(w) for w in words} & qtokens)
        if hit > n:
            best, n = name, hit
    return best


def _score(p: Passage, q: set[str]) -> float:
    if not q:
        return 0.0
    t = len(q & p.title_set)
    b = len(q & p.tset)
    return 3.0 * t + 1.0 * (b - t)


def _cite(p: Passage) -> dict:
    return {"title": p.title, "path": p.path, "kind": p.kind, "source": p.prov["source"],
            "last_verified": p.prov["last_verified"], "stale": p.prov["stale"]}


def _best_sentences(text: str, q: set[str], n: int = 2) -> str:
    sents = _sentences(text)
    ranked = sorted(sents, key=lambda s: -len(q & set(tokens(s))))
    chosen = [s for s in ranked[:n] if q & set(tokens(s))] or sents[:1]
    return " ".join(s for s in sents if s in chosen)


def answer(db: Session, question: str) -> dict:
    question = " ".join(question.split())
    if PREDICTIVE.search(question):
        return {"answered": False, "answer": PREDICTION, "citations": [], "reason": "prediction"}
    qt = set(tokens(question))
    if not qt:
        return {"answered": False, "answer": REFUSAL, "citations": [], "reason": "empty"}
    passages = build_passages(db)
    intent = _intent({stem(w) for w in re.findall(r"[a-z0-9]+", question.lower())})
    # find the entity the question is about: best title-bearing passage among entity kinds
    entities = [p for p in passages if p.kind in ("role", "sector", "skill", "company")]
    scored = sorted(((_score(p, qt), p) for p in entities), key=lambda x: -x[0])
    news = sorted(((_score(p, qt), p) for p in passages if p.kind == "news"), key=lambda x: -x[0])
    top_score, top = scored[0] if scored else (0, None)
    # require that the question's distinctive terms are actually covered
    if top is None or top_score < 3 or (len(qt & top.title_set) == 0):
        if news and news[0][0] >= 3 and len(qt & news[0][1].tset) >= 2:
            p = news[0][1]
            return {"answered": True, "answer": _best_sentences(p.text, qt), "citations": [_cite(p)], "reason": "news",
                    "link": p.extra.get("link")}
        return {"answered": False, "answer": REFUSAL, "citations": [], "reason": "no_match"}
    distinct = qt - {stem(w) for ws in INTENTS.values() for w in ws}
    if distinct and len(distinct & top.tset) / len(distinct) < 0.5:
        return {"answered": False, "answer": REFUSAL, "citations": [], "reason": "weak_match"}
    if top.kind == "role" and intent in ("requirements", "degrees", "hiring"):
        sub = next((p for p in passages if p.kind == intent and p.slug == top.slug), None)
        if sub is not None:
            return _compose_role(top, sub, intent)
        return {"answered": False, "answer": f"I do not have sourced {intent.replace('requirements', 'requirement')} "
                                             f"information for {top.title} yet.", "citations": [_cite(top)], "reason": "gap"}
    if top.kind == "skill" and intent == "learn":
        res = top.extra.get("resources", [])
        if res:
            lines = "; ".join(f"{t} ({prov}, {'free' if price == 0 else '₹' + str(price)})" for t, prov, _u, price in res[:4])
            return {"answered": True, "answer": f"Ways to learn {top.title}: {lines}.", "citations": [_cite(top)],
                    "reason": "skill_resources"}
    return {"answered": True, "answer": _best_sentences(top.text, qt), "citations": [_cite(top)], "reason": top.kind}


def _compose_role(role: Passage, sub: Passage, intent: str) -> dict:
    if intent == "requirements":
        names = {"mandatory": "Required", "common_preference": "Commonly preferred", "recommended": "Recommended",
                 "differentiator": "Stand-out extras"}
        parts = [f"{names[t]}: {', '.join(v)}." for t, v in sub.extra["lines"].items() if v]
        text = f"For {role.title}. " + " ".join(parts)
    elif intent == "degrees":
        text = f"Degrees listed as routes into {role.title}: {'; '.join(sub.extra['degrees'])}."
    else:
        text = f"Official hiring pages we have checked for {role.title}: " + "; ".join(
            f"{c} ({u}, checked {d})" for c, u, d in sub.extra["pages"]) + "."
    return {"answered": True, "answer": text, "citations": [_cite(sub)], "reason": f"role_{intent}"}


def record_unanswered(db: Session, question: str) -> None:
    norm = " ".join(tokens(question))[:300]
    if not norm:
        return
    now = datetime.now(timezone.utc)
    row = db.scalar(select(m.UnansweredQuestion).where(m.UnansweredQuestion.normalized == norm))
    if row is None:
        db.add(m.UnansweredQuestion(normalized=norm, example=question[:300], first_asked=now, last_asked=now))
    else:
        row.times_asked += 1
        row.last_asked = now
    db.commit()


def top_passages(db: Session, question: str, k: int = 5) -> list[dict]:
    """Published passages most relevant to a question, for grounding the optional AI companion.

    Includes lessons and global briefs as well as the careers content. Each passage keeps its path and source
    so the companion's citations can be shown to the student."""
    qt = set(tokens(question))
    if not qt:
        return []
    cands: list[tuple[float, dict]] = []
    for p in build_passages(db):
        if not p.text:
            continue
        sc = _score(p, qt)
        if sc >= 2:
            cands.append((sc, {"title": p.title, "path": p.path, "text": _best_sentences(p.text, qt, 3),
                               "kind": p.kind, "source": (p.prov.get("source") or {}).get("title"),
                               "last_verified": p.prov.get("last_verified")}))
    for les in db.scalars(select(m.Lesson).where(m.Lesson.status == PUB)):
        ts = set(tokens(les.title + " " + les.summary + " " + les.body))
        sc = 3.0 * len(qt & set(tokens(les.title))) + len(qt & ts)
        if sc >= 2:
            cands.append((sc, {"title": les.title, "path": f"/academy/{les.slug}", "kind": "lesson",
                               "text": _best_sentences(les.summary + " " + les.body, qt, 3),
                               "source": (les.source.title if les.source else None),
                               "last_verified": les.last_verified.isoformat() if les.last_verified else None}))
    for b in db.scalars(select(m.GlobalBrief).where(m.GlobalBrief.status == PUB)):
        body = f"{b.what_happened} {b.why_matters} {b.consequences}"
        ts = set(tokens(b.headline + " " + body))
        sc = 3.0 * len(qt & set(tokens(b.headline))) + len(qt & ts)
        if sc >= 2:
            cands.append((sc, {"title": b.headline, "path": f"/world/briefs/{b.slug}", "kind": "brief",
                               "text": _best_sentences(body, qt, 3), "source": (b.source.title if b.source else None),
                               "last_verified": b.last_verified.isoformat() if b.last_verified else None}))
    cands.sort(key=lambda x: -x[0])
    return [c[1] for c in cands[:k]]

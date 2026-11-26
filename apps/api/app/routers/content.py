"""Public, read-only routes for the learn / explore / practise / live modules. Only published rows are ever shown."""
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from .. import meta
from .. import models as m
from ..db import get_db
from ..deps import RateLimiter
from ..services import calc
from ..services.provenance import provenance
from ..services.safety import CRISIS_CHECKED_ON, CRISIS_RESOURCES
from ..services.scenario import public_node

router = APIRouter(prefix="/v1", tags=["content"])
PUB = m.Status.published
calc_limit = RateLimiter(60, 60)


def _like(term: str) -> str:
    return "%" + term.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_") + "%"


def _get(db: Session, model, slug: str):
    obj = db.scalar(select(model).where(model.slug == slug, model.status == PUB))
    if obj is None:
        raise HTTPException(404, "Not found")
    return obj


# ---------------------------------------------------------------- meta and coverage
@router.get("/meta")
def get_meta():
    return {"pillars": meta.PILLARS, "scenario_pillars": meta.SCENARIO_PILLARS, "boards": meta.BOARDS,
            "library_kinds": sorted(meta.LIBRARY_KINDS), "licence_status": meta.LICENCE_STATUS,
            "opportunity_kinds": sorted(meta.OPPORTUNITY_KINDS), "brief_categories": sorted(meta.BRIEF_CATEGORIES),
            "master_sections": meta.MASTER_SECTIONS, "application_status": meta.APPLICATION_STATUS,
            "mentor_kinds": sorted(meta.MENTOR_KINDS), "destinations": meta.DESTINATIONS}


@router.get("/crisis")
def crisis():
    """Always available, whether or not any wellness content has been published."""
    return {"resources": CRISIS_RESOURCES, "checked_on": CRISIS_CHECKED_ON,
            "note": "If you or someone near you is in immediate danger, call 112."}


@router.get("/content-coverage")
def coverage(db: Session = Depends(get_db)):
    """How much published content exists behind each of the 22 pillars. Honest about gaps."""
    def n(model, *where):
        return db.scalar(select(func.count()).select_from(model).where(model.status == PUB, *where)) or 0

    c = {"lessons": n(m.Lesson), "library": n(m.LibraryItem), "questions": n(m.Question), "assessments": n(m.Assessment),
         "scenarios": n(m.Scenario), "opportunities": n(m.Opportunity), "briefs": n(m.GlobalBrief),
         "countries": n(m.Country), "wellness": n(m.WellnessResource), "roles": n(m.Role), "sectors": n(m.Sector),
         "companies": n(m.Company), "skills": n(m.Skill), "resources": n(m.LearningResource),
         "qualifications": n(m.Qualification)}
    by = {1: c["library"], 2: c["lessons"], 3: n(m.Scenario, m.Scenario.pillar == "jugaad"), 4: c["roles"],
          5: c["companies"], 6: c["resources"], 7: None, 8: n(m.Question, m.Question.pillar == "interview"),
          9: n(m.Scenario, m.Scenario.pillar != "jugaad"), 10: c["briefs"], 11: n(m.Lesson, m.Lesson.pillar == "ai-era"),
          12: n(m.Lesson, m.Lesson.pillar == "life-skills"), 13: c["wellness"],
          14: n(m.Lesson, m.Lesson.pillar == "social"), 15: c["opportunities"], 16: None, 17: None, 18: None,
          19: None, 20: None, 21: c["assessments"], 22: None,
          23: n(m.Lesson, m.Lesson.pillar == "teamwork"), 24: n(m.Lesson, m.Lesson.pillar == "grooming"),
          25: n(m.Lesson, m.Lesson.pillar == "elocution"), 26: n(m.Lesson, m.Lesson.pillar == "growth"), 27: n(m.Lesson, m.Lesson.pillar == "entrepreneurship")}
    return {"counts": c, "pillars": [{"number": k, "name": name, "destination": dest, "path": path,
                                      "published_items": by[k]} for k, name, dest, path in meta.BLUEPRINT]}


@router.get("/skills")
def skills(q: str | None = Query(None, max_length=80), db: Session = Depends(get_db)):
    stmt = select(m.Skill).where(m.Skill.status == PUB)
    if q:
        stmt = stmt.where(or_(m.Skill.name.ilike(_like(q), escape="\\"), m.Skill.category.ilike(_like(q), escape="\\")))
    rows = db.scalars(stmt.order_by(m.Skill.category, m.Skill.name).limit(400)).all()
    return {"results": [{"slug": r.slug, "name": r.name, "category": r.category, "overview": r.overview} for r in rows]}


# ---------------------------------------------------------------- academy
def _lesson_out(x: m.Lesson, full: bool = False) -> dict:
    d = {"slug": x.slug, "pillar": x.pillar, "track": x.track, "title": x.title, "summary": x.summary, "level": x.level,
         "minutes": x.minutes, "language": x.language}
    if full:
        d |= {"body": x.body, "skill": x.skill.slug if getattr(x, "skill", None) else None, "provenance": provenance(x)}
    return d


@router.get("/lessons")
def lessons(pillar: str | None = None, track: str | None = None, level: str | None = None, language: str | None = None,
            q: str | None = Query(None, max_length=80), db: Session = Depends(get_db)):
    stmt = select(m.Lesson).where(m.Lesson.status == PUB)
    if pillar:
        stmt = stmt.where(m.Lesson.pillar == pillar)
    if track:
        stmt = stmt.where(m.Lesson.track == track)
    if level:
        stmt = stmt.where(m.Lesson.level == level)
    if language:
        stmt = stmt.where(m.Lesson.language == language)
    if q:
        stmt = stmt.where(or_(m.Lesson.title.ilike(_like(q), escape="\\"), m.Lesson.summary.ilike(_like(q), escape="\\")))
    rows = db.scalars(stmt.order_by(m.Lesson.pillar, m.Lesson.track, m.Lesson.position, m.Lesson.title).limit(300)).all()
    tracks: dict = {}
    for p, t, c in db.execute(select(m.Lesson.pillar, m.Lesson.track, func.count()).where(m.Lesson.status == PUB)
                              .group_by(m.Lesson.pillar, m.Lesson.track)):
        tracks.setdefault(p, {})[t] = c
    return {"results": [_lesson_out(r) for r in rows], "tracks": tracks, "pillars": meta.PILLARS}


@router.get("/lessons/{slug}")
def lesson(slug: str, db: Session = Depends(get_db)):
    x = _get(db, m.Lesson, slug)
    out = _lesson_out(x, full=True)
    out["next_in_track"] = [_lesson_out(y) for y in db.scalars(select(m.Lesson).where(
        m.Lesson.status == PUB, m.Lesson.pillar == x.pillar, m.Lesson.track == x.track, m.Lesson.id != x.id)
        .order_by(m.Lesson.position, m.Lesson.title).limit(6))]
    return out


# ---------------------------------------------------------------- library
def _lib_out(x: m.LibraryItem) -> dict:
    return {"slug": x.slug, "title": x.title, "authors": x.authors, "kind": x.kind, "subject": x.subject, "stream": x.stream,
            "language": x.language, "publisher": x.publisher, "access_url": x.access_url, "format": x.format,
            "level": x.level, "edition_year": x.edition_year,
            "licence": {"status": x.licence_status, "label": meta.LICENCE_STATUS.get(x.licence_status), "note": x.licence_note},
            "provenance": provenance(x)}


@router.get("/library")
def library(kind: str | None = None, subject: str | None = None, stream: str | None = None, language: str | None = None,
            level: str | None = None, q: str | None = Query(None, max_length=80), db: Session = Depends(get_db)):
    base = select(m.LibraryItem).where(m.LibraryItem.status == PUB)
    stmt = base
    for col, v in ((m.LibraryItem.kind, kind), (m.LibraryItem.subject, subject), (m.LibraryItem.stream, stream),
                   (m.LibraryItem.language, language), (m.LibraryItem.level, level)):
        if v:
            stmt = stmt.where(col == v)
    for word in (q or "").split()[:6]:  # every word must match somewhere, so "linear algebra beginner" narrows the list
        like = _like(word)
        stmt = stmt.where(or_(*(c.ilike(like, escape="\\") for c in (m.LibraryItem.title, m.LibraryItem.authors, m.LibraryItem.subject,
                                                                    m.LibraryItem.stream, m.LibraryItem.publisher, m.LibraryItem.level))))
    order = case({"beginner": 1, "intermediate": 2, "advanced": 3}, value=m.LibraryItem.level, else_=4)  # a beginner-to-advanced reading path
    rows = db.scalars(stmt.order_by(m.LibraryItem.subject, order, m.LibraryItem.title).limit(300)).all()

    def facet(col):
        return {k: c for k, c in db.execute(select(col, func.count()).where(m.LibraryItem.status == PUB, col.is_not(None))
                                            .group_by(col).order_by(col))}
    return {"results": [_lib_out(r) for r in rows],
            "facets": {"kind": facet(m.LibraryItem.kind), "subject": facet(m.LibraryItem.subject),
                       "language": facet(m.LibraryItem.language), "stream": facet(m.LibraryItem.stream)},
            "policy": "Samarthya links to readings that are open access, in the public domain, or offered free by their "
                      "publisher or institution. It does not host or copy copyrighted books. Each item shows its legal basis."}


@router.get("/library/{slug}")
def library_item(slug: str, db: Session = Depends(get_db)):
    return _lib_out(_get(db, m.LibraryItem, slug))


# ---------------------------------------------------------------- opportunities
def _opp_out(x: m.Opportunity, full: bool = True) -> dict:
    d = {"slug": x.slug, "title": x.title, "organisation": x.organisation, "kind": x.kind, "location": x.location,
         "mode": x.mode, "stipend": x.stipend, "duration": x.duration_text, "deadline": x.deadline.isoformat() if x.deadline else None,
         "rolling": x.rolling, "min_year": x.min_year, "max_year": x.max_year, "sector": x.sector.slug if x.sector else None}
    if full:
        d |= {"description": x.description, "eligibility": x.eligibility, "streams": x.streams, "skills": x.skills,
              "selection_process": x.selection_process, "apply_url": x.apply_url, "provenance": provenance(x)}
    return d


def open_opportunities():
    return (m.Opportunity.status == PUB) & (m.Opportunity.rolling.is_(True) | (m.Opportunity.deadline >= date.today()))


@router.get("/opportunities")
def opportunities(kind: str | None = None, mode: str | None = None, year: int | None = Query(None, ge=1, le=6),
                  stream: str | None = None, q: str | None = Query(None, max_length=80), location: str | None = Query(None, max_length=80),
                  db: Session = Depends(get_db)):
    stmt = select(m.Opportunity).where(open_opportunities())
    if kind:
        stmt = stmt.where(m.Opportunity.kind == kind)
    if mode:
        stmt = stmt.where(m.Opportunity.mode == mode)
    if year:
        stmt = stmt.where(or_(m.Opportunity.min_year.is_(None), m.Opportunity.min_year <= year),
                          or_(m.Opportunity.max_year.is_(None), m.Opportunity.max_year >= year))
    if location:
        stmt = stmt.where(m.Opportunity.location.ilike(_like(location), escape="\\"))
    if q:
        stmt = stmt.where(or_(m.Opportunity.title.ilike(_like(q), escape="\\"), m.Opportunity.organisation.ilike(_like(q), escape="\\")))
    rows = db.scalars(stmt.order_by(m.Opportunity.deadline.asc().nullslast(), m.Opportunity.title).limit(300)).all()
    if stream:  # streams is a JSON list; filter in Python so it works on every database
        rows = [r for r in rows if not r.streams or stream in r.streams]
    kinds = {k: c for k, c in db.execute(select(m.Opportunity.kind, func.count()).where(open_opportunities())
                                         .group_by(m.Opportunity.kind))}
    return {"results": [_opp_out(r, full=False) for r in rows], "kinds": kinds,
            "note": "Expired opportunities disappear automatically. Always confirm details on the official page before applying."}


@router.get("/opportunities/{slug}")
def opportunity(slug: str, db: Session = Depends(get_db)):
    x = _get(db, m.Opportunity, slug)
    out = _opp_out(x)
    out["expired"] = bool(not x.rolling and x.deadline and x.deadline < date.today())
    return out


# ---------------------------------------------------------------- global intelligence
def _brief_out(x: m.GlobalBrief, full: bool = True) -> dict:
    d = {"slug": x.slug, "category": x.category, "region": x.region, "event_date": x.event_date.isoformat(), "headline": x.headline}
    if full:
        d |= {"sections": [{"title": t, "text": getattr(x, f)} for t, f in (
            ("What happened", "what_happened"), ("What led to it", "what_led"), ("Why it matters", "why_matters"),
            ("Who is affected", "who_affected"), ("Economic, political and social consequences", "consequences"),
            ("What could happen next", "what_next"), ("What to investigate further", "investigate"))],
              "connects_to": x.connects_to, "provenance": provenance(x)}
    return d


@router.get("/briefs")
def briefs(category: str | None = None, region: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.GlobalBrief).where(m.GlobalBrief.status == PUB)
    if category:
        stmt = stmt.where(m.GlobalBrief.category == category)
    if region:
        stmt = stmt.where(m.GlobalBrief.region == region)
    rows = db.scalars(stmt.order_by(m.GlobalBrief.event_date.desc()).limit(200)).all()
    cats = {k: c for k, c in db.execute(select(m.GlobalBrief.category, func.count()).where(m.GlobalBrief.status == PUB)
                                        .group_by(m.GlobalBrief.category))}
    return {"results": [_brief_out(r, full=False) for r in rows], "categories": cats}


@router.get("/impact-map")
def impact_map(db: Session = Depends(get_db)):
    """Connect-the-dots view: published briefs joined where they share a category or a topic tag. Nothing is added
    that an editor did not already tag, so every link can be traced to the briefs and their sources."""
    rows = db.scalars(select(m.GlobalBrief).where(m.GlobalBrief.status == PUB).order_by(m.GlobalBrief.event_date.desc()).limit(40)).all()
    nodes = [{"slug": b.slug, "headline": b.headline, "category": b.category, "date": b.event_date.isoformat()} for b in rows]
    edges = []
    for i, a in enumerate(rows):
        ta = {a.category, *(a.connects_to or [])}
        for b in rows[i + 1:]:
            shared = sorted(ta & {b.category, *(b.connects_to or [])})
            if shared:
                edges.append({"from": a.slug, "to": b.slug, "because": shared, "strength": len(shared)})
    return {"nodes": nodes, "edges": edges[:200],
            "note": "Links appear only where editors gave two briefs the same category or topic. They show connection, not proof that one event caused another."}


@router.get("/briefs/{slug}")
def brief(slug: str, db: Session = Depends(get_db)):
    x = _get(db, m.GlobalBrief, slug)
    out = _brief_out(x)
    tags = set(x.connects_to or [])
    out["related"] = [_brief_out(r, full=False) for r in db.scalars(select(m.GlobalBrief).where(
        m.GlobalBrief.status == PUB, m.GlobalBrief.id != x.id).order_by(m.GlobalBrief.event_date.desc()).limit(60))
        if r.category in tags or tags & set(r.connects_to or []) or r.category == x.category][:6]
    return out


@router.get("/countries")
def countries(region: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Country).where(m.Country.status == PUB)
    if region:
        stmt = stmt.where(m.Country.region == region)
    rows = db.scalars(stmt.order_by(m.Country.name)).all()
    return {"results": [{"slug": c.slug, "name": c.name, "iso_numeric": c.iso_numeric, "region": c.region} for c in rows]}


@router.get("/countries/{slug}")
def country(slug: str, db: Session = Depends(get_db)):
    c = _get(db, m.Country, slug)
    events = db.scalars(select(m.TimelineEvent).where(m.TimelineEvent.status == PUB, m.TimelineEvent.country_id == c.id)
                        .order_by(m.TimelineEvent.event_year)).all()
    return {"slug": c.slug, "name": c.name, "iso_numeric": c.iso_numeric, "region": c.region, "capital": c.capital,
            "summary": c.summary, "facts": c.facts, "provenance": provenance(c),
            "timeline": [{"year": e.event_year, "title": e.title, "summary": e.summary} for e in events]}


@router.get("/timeline")
def timeline(region: str | None = None, category: str | None = None, start: int | None = None, end: int | None = None,
             db: Session = Depends(get_db)):
    stmt = select(m.TimelineEvent).where(m.TimelineEvent.status == PUB)
    for col, v in ((m.TimelineEvent.region, region), (m.TimelineEvent.category, category)):
        if v:
            stmt = stmt.where(col == v)
    if start is not None:
        stmt = stmt.where(m.TimelineEvent.event_year >= start)
    if end is not None:
        stmt = stmt.where(m.TimelineEvent.event_year <= end)
    rows = db.scalars(stmt.order_by(m.TimelineEvent.event_year).limit(500)).all()
    return {"results": [{"slug": e.slug, "year": e.event_year, "title": e.title, "summary": e.summary, "region": e.region,
                         "category": e.category, "provenance": provenance(e)} for e in rows]}


# ---------------------------------------------------------------- practise (public metadata only)
@router.get("/assessments")
def assessments(pillar: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Assessment).where(m.Assessment.status == PUB)
    if pillar:
        stmt = stmt.where(m.Assessment.pillar == pillar)
    return {"results": [_assessment_out(a) for a in db.scalars(stmt.order_by(m.Assessment.title))]}


def _assessment_out(a: m.Assessment) -> dict:
    cred = {"internal": "Samarthya internal badge. Not an accredited qualification.",
            "partner": f"Partner-issued credential by {a.issuer}.", "accredited": f"Accredited credential issued by {a.issuer}."}
    return {"slug": a.slug, "title": a.title, "pillar": a.pillar, "description": a.description,
            "duration_minutes": a.duration_minutes, "questions": len(a.question_slugs or []),
            "credential": {"type": a.credential_type, "issuer": a.issuer, "official_url": a.official_url,
                           "statement": cred.get(a.credential_type, "")}}


@router.get("/assessments/{slug}")
def assessment(slug: str, db: Session = Depends(get_db)):
    return _assessment_out(_get(db, m.Assessment, slug)) | {"provenance": provenance(_get(db, m.Assessment, slug))}


@router.get("/scenarios")
def scenarios(pillar: str | None = None, sector: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Scenario).where(m.Scenario.status == PUB)
    if pillar:
        stmt = stmt.where(m.Scenario.pillar == pillar)
    if sector:
        stmt = stmt.join(m.Sector, m.Sector.id == m.Scenario.sector_id).where(m.Sector.slug == sector)
    rows = db.scalars(stmt.order_by(m.Scenario.title).limit(300)).all()
    return {"results": [_scenario_out(r) for r in rows], "pillars": meta.SCENARIO_PILLARS}


def _scenario_out(s: m.Scenario, full: bool = False) -> dict:
    d = {"slug": s.slug, "title": s.title, "pillar": s.pillar, "pillar_label": meta.SCENARIO_PILLARS.get(s.pillar),
         "sector": s.sector.slug if s.sector else None, "difficulty": s.difficulty, "minutes": s.minutes,
         "real_case": s.real_case, "kind_note": "Based on a documented real event." if s.real_case else "A constructed exercise, not a real event."}
    if full:
        d |= {"brief": s.brief, "dimensions": s.dimensions, "provenance": provenance(s)}
    return d


@router.get("/scenarios/{slug}")
def scenario(slug: str, db: Session = Depends(get_db)):
    s = _get(db, m.Scenario, slug)
    return _scenario_out(s, full=True) | {"start": public_node(s.nodes[0])}


# ---------------------------------------------------------------- live
@router.get("/wellness/resources")
def wellness_resources(kind: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.WellnessResource).where(m.WellnessResource.status == PUB)
    if kind:
        stmt = stmt.where(m.WellnessResource.kind == kind)
    rows = db.scalars(stmt.order_by(m.WellnessResource.kind, m.WellnessResource.title)).all()
    return {"results": [{"slug": r.slug, "title": r.title, "kind": r.kind, "summary": r.summary, "phone": r.phone,
                         "url": r.url, "hours": r.hours, "languages": r.languages, "cost": r.cost, "audience": r.audience,
                         "region": r.region, "provenance": provenance(r)} for r in rows]}


_CALCS = {"emi": calc.emi, "growth": calc.compound, "inflation": calc.real_value, "budget": calc.budget, "goal": calc.savings_goal, "ctc": calc.ctc, "offers": calc.offer_compare}


@router.post("/calc/{name}")
def calculate(name: str, body: dict = Body(...), _=Depends(calc_limit)):
    fn = _CALCS.get(name)
    if fn is None:
        raise HTTPException(404, "Unknown calculator")
    try:
        return fn(**body)
    except (ValueError, TypeError) as e:
        raise HTTPException(422, str(e) if isinstance(e, ValueError) else "Some values are missing or not numbers") from e

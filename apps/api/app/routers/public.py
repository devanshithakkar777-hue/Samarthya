from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from pydantic import BaseModel, Field

from ..deps import RateLimiter
from ..services import ask as ask_service
from ..schemas import FitRequest
from ..services.fit import compute_fit
from ..services.provenance import provenance

router = APIRouter(prefix="/v1", tags=["public"])
fit_limit = RateLimiter(limit=60, window_seconds=60)
PUB = m.Status.published


def _get(db: Session, model, slug: str):
    obj = db.scalar(select(model).where(model.slug == slug, model.status == PUB))
    if obj is None:
        raise HTTPException(404, "Not found")
    return obj


def _role_card(r: m.Role) -> dict:
    return {"id": r.id, "slug": r.slug, "title": r.title, "job_family": r.job_family, "level": r.level,
            "sector": {"slug": r.sector.slug, "name": r.sector.name}}


@router.get("/qualifications")
def qualifications(db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Qualification).where(m.Qualification.status == PUB)
                      .order_by(m.Qualification.level, m.Qualification.degree)).all()
    return [{"id": q.id, "slug": q.slug, "degree": q.degree, "level": q.level,
             "specialization": q.specialization, "duration_years": q.duration_years, "kind": q.kind, "stream": q.stream, "awarding_body": q.awarding_body} for q in rows]


@router.get("/sectors")
def sectors(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(m.Role.sector_id, func.count()).where(m.Role.status == PUB)
                             .group_by(m.Role.sector_id)).all())
    rows = db.scalars(select(m.Sector).where(m.Sector.status == PUB).order_by(m.Sector.name)).all()
    return [{"id": s.id, "slug": s.slug, "name": s.name, "summary": s.summary, "role_count": counts.get(s.id, 0)}
            for s in rows]


@router.get("/sectors/{slug}")
def sector_detail(slug: str, db: Session = Depends(get_db)):
    s = _get(db, m.Sector, slug)
    roles = db.scalars(select(m.Role).where(m.Role.sector_id == s.id, m.Role.status == PUB)
                       .options(selectinload(m.Role.sector)).order_by(m.Role.title)).all()
    routes = db.scalars(select(m.QualificationSector).where(m.QualificationSector.sector_id == s.id)
                        .options(selectinload(m.QualificationSector.qualification),
                                 selectinload(m.QualificationSector.source))
                        .order_by(m.QualificationSector.strength.desc())).all()
    return {"id": s.id, "slug": s.slug, "name": s.name, "summary": s.summary, **provenance(s),
            "roles": [_role_card(r) for r in roles],
            "education_routes": [
                {"qualification": {"slug": q.qualification.slug, "degree": q.qualification.degree,
                                   "specialization": q.qualification.specialization},
                 "strength": q.strength, "reason": q.reason, **provenance(q)}
                for q in routes if q.qualification.status == PUB]}


@router.get("/roles")
def roles(sector: str | None = None, db: Session = Depends(get_db)):
    q = select(m.Role).where(m.Role.status == PUB).options(selectinload(m.Role.sector)).order_by(m.Role.title)
    if sector:
        q = q.join(m.Sector).where(m.Sector.slug == sector)
    return [_role_card(r) for r in db.scalars(q).all() if r.sector.status == PUB]


@router.get("/roles/{slug}")
def role_detail(slug: str, db: Session = Depends(get_db)):
    r = db.scalar(select(m.Role).where(m.Role.slug == slug, m.Role.status == PUB).options(
        selectinload(m.Role.sector), selectinload(m.Role.source),
        selectinload(m.Role.requirements).selectinload(m.RoleRequirement.skill),
        selectinload(m.Role.qualifications).selectinload(m.RoleQualification.qualification),
        selectinload(m.Role.hiring).selectinload(m.CompanyRole.company)))
    if r is None:
        raise HTTPException(404, "Not found")
    tiers: dict[str, list] = {t.value: [] for t in m.Tier}
    for req in r.requirements:
        tiers[req.tier.value].append({
            "id": req.id, "type": req.type.value, "label": req.label, "note": req.note,
            "skill": {"slug": req.skill.slug, "name": req.skill.name}
            if req.skill is not None and req.skill.status == PUB else None})
    return {**_role_card(r), "description": r.description, "progression": r.progression, **provenance(r),
            "requirements": tiers,
            "entry_degrees": [{"slug": rq.qualification.slug, "degree": rq.qualification.degree,
                               "specialization": rq.qualification.specialization, "note": rq.note}
                              for rq in r.qualifications if rq.qualification.status == PUB],
            "employers": [{"company": h.company.name, "slug": h.company.slug, "careers_url": h.careers_url,
                           "last_verified": h.last_verified.isoformat()}
                          for h in r.hiring if h.company.status == PUB]}


@router.get("/companies")
def companies(db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Company).where(m.Company.status == PUB).order_by(m.Company.name)).all()
    return [{"id": c.id, "slug": c.slug, "name": c.name, "summary": c.summary,
             "listing_status": c.listing_status} for c in rows]


@router.get("/companies/{slug}")
def company_detail(slug: str, db: Session = Depends(get_db)):
    c = db.scalar(select(m.Company).where(m.Company.slug == slug, m.Company.status == PUB).options(
        selectinload(m.Company.source), selectinload(m.Company.hiring).selectinload(m.CompanyRole.role)))
    if c is None:
        raise HTTPException(404, "Not found")
    return {"id": c.id, "slug": c.slug, "name": c.name, "summary": c.summary, "cin": c.cin,
            "listing_status": c.listing_status, "industry_code": c.industry_code, "website": c.website,
            **provenance(c),
            "roles": [{"slug": h.role.slug, "title": h.role.title, "careers_url": h.careers_url,
                       "last_verified": h.last_verified.isoformat()}
                      for h in c.hiring if h.role.status == PUB]}


@router.get("/skills/{slug}")
def skill_detail(slug: str, db: Session = Depends(get_db)):
    s = db.scalar(select(m.Skill).where(m.Skill.slug == slug, m.Skill.status == PUB)
                  .options(selectinload(m.Skill.source), selectinload(m.Skill.resources)
                           .selectinload(m.LearningResource.source)))
    if s is None:
        raise HTTPException(404, "Not found")
    order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    res = sorted((r for r in s.resources if r.status == PUB),
                 key=lambda r: (order.get(r.level.lower(), 3), r.price_inr, r.title))
    return {"id": s.id, "slug": s.slug, "name": s.name, "category": s.category, "overview": s.overview,
            **provenance(s),
            "resources": [{"id": r.id, "title": r.title, "provider": r.provider, "url": r.url, "format": r.format,
                           "level": r.level, "price_inr": r.price_inr, "free": r.price_inr == 0,
                           "language": r.language, "duration_hours": r.duration_hours,
                           "certificate": r.certificate, "sponsored": r.sponsored, **provenance(r)}
                          for r in res]}


@router.get("/roadmap")
def roadmap(qualification: str, db: Session = Depends(get_db)):
    q = _get(db, m.Qualification, qualification)
    steps = db.scalars(select(m.RoadmapStep).where(m.RoadmapStep.qualification_id == q.id,
                                                   m.RoadmapStep.status == PUB)
                       .options(selectinload(m.RoadmapStep.source))
                       .order_by(m.RoadmapStep.year_of_study, m.RoadmapStep.position)).all()
    years: dict[int, list] = {}
    for s in steps:
        years.setdefault(s.year_of_study, []).append(
            {"id": s.id, "title": s.title, "detail": s.detail, **provenance(s)})
    return {"qualification": {"slug": q.slug, "degree": q.degree, "duration_years": q.duration_years},
            "years": [{"year": y, "steps": v} for y, v in sorted(years.items())]}


@router.get("/briefing")
def briefing(sector: str | None = None, db: Session = Depends(get_db)):
    q = (select(m.NewsItem).where(m.NewsItem.status == PUB)
         .options(selectinload(m.NewsItem.sector), selectinload(m.NewsItem.source))
         .order_by(m.NewsItem.event_date.desc()).limit(30))
    if sector:
        q = q.join(m.Sector, m.NewsItem.sector_id == m.Sector.id).where(m.Sector.slug == sector)
    items = db.scalars(q).all()
    sector_ids = {n.sector_id for n in items if n.sector_id}
    roles_by_sector: dict[int, list] = {}
    if sector_ids:
        for r in db.scalars(select(m.Role).where(m.Role.sector_id.in_(sector_ids), m.Role.status == PUB)
                            .order_by(m.Role.title)):
            roles_by_sector.setdefault(r.sector_id, []).append({"slug": r.slug, "title": r.title})
    return [{"id": n.id, "headline": n.headline, "summary": n.summary, "why_it_matters": n.why_it_matters,
             "link": n.link, "event_date": n.event_date.isoformat(),
             "week_of": (n.event_date - timedelta(days=n.event_date.weekday())).isoformat(),
             "sector": {"slug": n.sector.slug, "name": n.sector.name} if n.sector else None,
             "related_roles": roles_by_sector.get(n.sector_id, [])[:3] if n.sector_id else [],
             **provenance(n)} for n in items]


def _like(term: str) -> str:
    return "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


@router.get("/search")
def search(q: str = Query(min_length=2, max_length=80), db: Session = Depends(get_db)):
    pat = _like(q.strip())
    def run(model, *cols):
        return db.scalars(select(model).where(model.status == PUB,
                                              or_(*[c.ilike(pat, escape="\\") for c in cols])).limit(10)).all()
    return {
        "sectors": [{"slug": s.slug, "name": s.name} for s in run(m.Sector, m.Sector.name, m.Sector.summary)],
        "roles": [{"slug": r.slug, "title": r.title} for r in run(m.Role, m.Role.title, m.Role.job_family)],
        "companies": [{"slug": c.slug, "name": c.name} for c in run(m.Company, m.Company.name)],
        "skills": [{"slug": s.slug, "name": s.name} for s in run(m.Skill, m.Skill.name, m.Skill.category)],
    }


@router.get("/coverage")
def coverage(db: Session = Depends(get_db)):
    """What the knowledge base actually holds today, so the product never overstates its coverage."""
    def count(model):
        return db.scalar(select(func.count()).select_from(model).where(model.status == PUB)) or 0
    oldest = db.scalar(select(func.min(m.Role.last_verified)).where(m.Role.status == PUB))
    return {"qualifications": count(m.Qualification), "sectors": count(m.Sector), "roles": count(m.Role),
            "companies": count(m.Company), "skills": count(m.Skill), "resources": count(m.LearningResource),
            "roadmap_steps": count(m.RoadmapStep), "briefing_items": count(m.NewsItem),
            "oldest_role_verification": oldest.isoformat() if oldest else None,
            "as_of": date.today().isoformat()}


@router.post("/fit", dependencies=[Depends(fit_limit)])
def fit(body: FitRequest, db: Session = Depends(get_db)):
    p = body.profile
    return {"results": compute_fit(db, p.qualification, p.year_of_study, p.interests, p.skills,
                                   body.completed_requirement_ids, body.sort),
            "note": "Guidance, not a prediction. Four separate answers; there is no single score."}


ask_limit = RateLimiter(limit=20, window_seconds=60)


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=300)


@router.post("/ask", dependencies=[Depends(ask_limit)])
def ask(body: AskIn, db: Session = Depends(get_db)):
    """Answers only from published, sourced facts, with citations. Otherwise a plain refusal."""
    out = ask_service.answer(db, body.question)
    if not out["answered"] and out.get("reason") in ("no_match", "weak_match", "empty", "gap"):
        ask_service.record_unanswered(db, body.question)
    out["note"] = "Answers are copied from sourced pages. Always confirm on the official page before you act."
    return out


# ---- Education & Qualification Explorer ----
K = m.Qualification.kind
LV = m.Qualification.level
STAGES = {  # starting filters only; eligibility must always be confirmed with the awarding body
    "after-10": K.in_(["certificate", "diploma"]),
    "after-12": or_(and_(K == "degree", LV == "undergraduate"), K.in_(["diploma", "certificate", "professional_qualification"])),
    "pursuing": K.in_(["certification", "professional_qualification", "examination", "diploma"]),
    "graduate": or_(and_(K == "degree", LV == "postgraduate"), K.in_(["professional_qualification", "diploma", "examination", "certification"])),
    "working": K.in_(["certification", "professional_qualification", "diploma", "examination", "licence"]),
    "research": LV == "doctoral",
}
FIELDS_HELD = ("name", "type", "stream", "awarding_body", "level", "duration_years")


@router.get("/pathways")
def pathways(stage: str | None = None, stream: str | None = None, kind: str | None = None,
             q: str | None = Query(None, max_length=80), db: Session = Depends(get_db)):
    if stage is not None and stage not in STAGES:
        raise HTTPException(422, "Unknown stage")
    base = select(m.Qualification).where(m.Qualification.status == PUB)
    if stage:
        base = base.where(STAGES[stage])
    if q:
        base = base.where(m.Qualification.degree.ilike(f"%{q.strip()}%"))
    scoped = base  # facet counts reflect the other filters, not their own
    rows_q = base
    if stream:
        rows_q = rows_q.where(m.Qualification.stream.is_(None) if stream == "Not yet assigned"
                              else m.Qualification.stream == stream)
    if kind:
        rows_q = rows_q.where(m.Qualification.kind == kind)
    rows = db.scalars(rows_q.order_by(m.Qualification.degree).limit(300)).all()
    sub = scoped.subquery()
    streams = dict(db.execute(select(sub.c.stream, func.count()).group_by(sub.c.stream)).all())
    kinds = dict(db.execute(select(sub.c.kind, func.count()).group_by(sub.c.kind)).all())
    return {"items": [{"slug": r.slug, "name": r.degree, "kind": r.kind, "stream": r.stream, "level": r.level,
                       "awarding_body": r.awarding_body, "duration_years": r.duration_years} for r in rows],
            "total": len(rows), "truncated": len(rows) == 300,
            "streams": {k or "Not yet assigned": v for k, v in sorted(streams.items(), key=lambda x: (x[0] is None, x[0] or ""))},
            "kinds": kinds}


@router.get("/pathways/{slug}")
def pathway_detail(slug: str, db: Session = Depends(get_db)):
    qual = db.scalar(select(m.Qualification).where(m.Qualification.slug == slug, m.Qualification.status == PUB)
                     .options(selectinload(m.Qualification.source)))
    if qual is None:
        raise HTTPException(404, "Not found")
    sectors = db.scalars(select(m.QualificationSector).where(m.QualificationSector.qualification_id == qual.id)
                         .options(selectinload(m.QualificationSector.sector)).order_by(m.QualificationSector.strength.desc())).all()
    roles = db.scalars(select(m.Role).join(m.RoleQualification, m.RoleQualification.role_id == m.Role.id)
                       .where(m.RoleQualification.qualification_id == qual.id, m.Role.status == PUB)
                       .order_by(m.Role.title)).all()
    return {"slug": qual.slug, "name": qual.degree, "kind": qual.kind, "stream": qual.stream, "level": qual.level,
            "specialization": qual.specialization, "awarding_body": qual.awarding_body, "duration_years": qual.duration_years,
            "eligibility": qual.eligibility, "entry_route": qual.entry_route, "training": qual.training,
            "recognition": qual.recognition, "cost_note": qual.cost_note, "official_url": qual.official_url,
            # directory fields Samarthya does not hold yet; the page says so instead of guessing
            "not_yet_verified": [k for k in ("eligibility", "entry_route", "training", "recognition", "cost_note", "official_url")
                                 if not getattr(qual, k)] + ["syllabus", "further_education", "alternative_pathways"],
            "sectors": [{"slug": x.sector.slug, "name": x.sector.name, "reason": x.reason}
                        for x in sectors if x.sector.status == PUB],
            "roles": [{"slug": r.slug, "title": r.title} for r in roles],
            **provenance(qual)}

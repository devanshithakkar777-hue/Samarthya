"""Rule-based fit engine.

Four separate answers per role, never combined into one score:
  eligibility   does the student meet the listed entry route?
  compatibility how closely do the role and the student's interests and skills match?
  readiness     how much preparation is left, counted by requirement tier?
  opportunity   which employers have a careers page for this role? (links only, no live openings)
Each answer carries plain reasons so the student can see why.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    CompanyRole,
    Qualification,
    QualificationSector,
    RequirementType,
    Role,
    RoleRequirement,
    Status,
    Tier,
)
from .provenance import provenance

ORDER = {"eligible": 0, "open": 1, "unknown": 2, "not_listed": 3,
         "strong": 0, "partial": 1, "low": 3,
         "close": 0, "some_preparation": 1, "substantial_preparation": 2, "no_requirements_listed": 2}


def _eligibility(role: Role, qual: Qualification | None) -> dict:
    listed = [rq.qualification for rq in role.qualifications if rq.qualification.status == Status.published]
    listed_names = [q.degree + (f" ({q.specialization})" if q.specialization else "") for q in listed]
    if not listed:
        return {"label": "open", "reasons": ["No specific degree is listed for this role."], "listed_degrees": []}
    if qual is None:
        return {"label": "unknown", "reasons": ["Add your degree to see whether it is a listed route."],
                "listed_degrees": listed_names}
    if any(q.id == qual.id for q in listed):
        return {"label": "eligible", "reasons": [f"{qual.degree} is a listed entry route."],
                "listed_degrees": listed_names}
    return {"label": "not_listed",
            "reasons": ["Your degree is not among the routes listed for this role. "
                        "Other routes may exist; check the employer's own requirements."],
            "listed_degrees": listed_names}


def _compatibility(role: Role, profile_interests: set[str], profile_skills: set[str],
                   qs_strength: dict[int, QualificationSector], qual: Qualification | None) -> dict:
    reasons: list[str] = []
    signals = 0
    if not profile_interests and not profile_skills and qual is None:
        return {"label": "unknown", "reasons": ["Add your degree, interests or skills to see how well this matches."]}
    if role.sector.slug in profile_interests:
        signals += 2
        reasons.append(f"You are interested in {role.sector.name}.")
    skill_reqs = [r for r in role.requirements if r.type == RequirementType.skill and r.skill is not None]
    matched = [r.skill.name for r in skill_reqs if r.skill.slug in profile_skills]
    if matched:
        signals += 1
        reasons.append("You report skills this role asks for: " + ", ".join(sorted(set(matched))) + ".")
    qs = qs_strength.get(role.sector_id)
    if qs is not None and qs.strength >= 2:
        signals += 1
        reasons.append(qs.reason)
    if signals >= 3:
        label = "strong"
    elif signals >= 1:
        label = "partial"
    else:
        label = "low"
        reasons.append("Nothing in your profile points to this role yet.")
    return {"label": label, "reasons": reasons}


def _readiness(role: Role, completed: set[int], profile_skills: set[str]) -> dict:
    tiers: dict[str, dict] = {t.value: {"done": 0, "total": 0} for t in Tier}
    outstanding: list[dict] = []
    for r in role.requirements:
        t = tiers[r.tier.value]
        t["total"] += 1
        covered = r.id in completed or (r.skill is not None and r.skill.slug in profile_skills)
        if covered:
            t["done"] += 1
        elif r.tier in (Tier.mandatory, Tier.common_preference):
            outstanding.append({"id": r.id, "label": r.label, "tier": r.tier.value, "type": r.type.value})
    core_total = tiers["mandatory"]["total"] + tiers["common_preference"]["total"]
    core_done = tiers["mandatory"]["done"] + tiers["common_preference"]["done"]
    if core_total == 0:
        label, reason = "no_requirements_listed", "No mandatory or commonly expected items are listed yet."
    else:
        ratio = core_done / core_total
        label = "close" if ratio >= 0.8 else "some_preparation" if ratio >= 0.4 else "substantial_preparation"
        reason = f"{core_done} of {core_total} mandatory and commonly expected items are covered."
    return {"label": label, "reasons": [reason], "by_tier": tiers, "outstanding": outstanding[:8]}


def _opportunity(role: Role) -> dict:
    pages = [{"company": h.company.name, "company_slug": h.company.slug, "careers_url": h.careers_url,
              "last_verified": h.last_verified.isoformat()}
             for h in role.hiring if h.company.status == Status.published]
    if not pages:
        return {"label": "none_listed", "reasons": ["No employer careers pages are listed for this role yet."],
                "hiring_pages": []}
    return {"label": "pages_listed",
            "reasons": [f"{len(pages)} employer careers page(s) listed. We link to them; we do not show live openings."],
            "hiring_pages": pages}


def compute_fit(db: Session, qualification_slug: str | None, year: int | None, interests: list[str],
                skills: list[str], completed: list[int], sort: str = "eligibility") -> list[dict]:
    qual = None
    if qualification_slug:
        qual = db.scalar(select(Qualification).where(Qualification.slug == qualification_slug,
                                                     Qualification.status == Status.published))
    roles = db.scalars(
        select(Role).where(Role.status == Status.published)
        .options(selectinload(Role.sector), selectinload(Role.source),
                 selectinload(Role.requirements).selectinload(RoleRequirement.skill),
                 selectinload(Role.qualifications), selectinload(Role.hiring).selectinload(CompanyRole.company))
    ).unique().all()

    qs_by_sector: dict[int, QualificationSector] = {}
    if qual is not None:
        for qs in db.scalars(select(QualificationSector).where(QualificationSector.qualification_id == qual.id)):
            qs_by_sector[qs.sector_id] = qs

    i_set, s_set, done = set(interests), set(skills), set(completed)
    out = []
    for role in roles:
        if role.sector.status != Status.published:
            continue
        out.append({
            "role": {"id": role.id, "slug": role.slug, "title": role.title, "level": role.level,
                     "sector": {"slug": role.sector.slug, "name": role.sector.name},
                     **provenance(role)},
            "eligibility": _eligibility(role, qual),
            "compatibility": _compatibility(role, i_set, s_set, qs_by_sector, qual),
            "readiness": _readiness(role, done, s_set),
            "opportunity": _opportunity(role),
        })

    def key(item):
        primary = ORDER.get(item[sort]["label"], 5)
        return (primary, ORDER.get(item["compatibility"]["label"], 5),
                ORDER.get(item["readiness"]["label"], 5), item["role"]["title"])

    out.sort(key=key)
    return out

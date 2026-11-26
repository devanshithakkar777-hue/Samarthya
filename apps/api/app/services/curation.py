"""Editorial workflow: draft, review, publish. Generic over the content tables."""
import enum
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import inspect, select
from sqlalchemy import JSON
from sqlalchemy import Date as SADate
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Session

from .. import models as m
from ..config import get_settings
from ..meta import CHOICES, LICENCE_STATUS

# name -> (model, editable fields)
REVIEWABLE: dict[str, tuple[type, set[str]]] = {
    "qualifications": (m.Qualification, {"slug", "degree", "level", "specialization", "duration_years",
                                         "kind", "stream", "awarding_body", "eligibility", "entry_route", "training",
                                         "recognition", "cost_note", "official_url",
                                         "source_id", "last_verified"}),
    "sectors": (m.Sector, {"slug", "name", "summary", "parent_id", "source_id", "last_verified"}),
    "roles": (m.Role, {"slug", "title", "job_family", "sector_id", "level", "description", "progression",
                       "source_id", "last_verified"}),
    "skills": (m.Skill, {"slug", "name", "category", "overview", "source_id", "last_verified"}),
    "companies": (m.Company, {"slug", "name", "cin", "listing_status", "industry_code", "summary", "website",
                              "source_id", "last_verified"}),
    "resources": (m.LearningResource, {"skill_id", "title", "provider", "url", "format", "level", "price_inr",
                                       "language", "duration_hours", "certificate", "sponsored", "source_id",
                                       "last_verified"}),
    "roadmap_steps": (m.RoadmapStep, {"qualification_id", "year_of_study", "title", "detail", "position",
                                      "source_id", "last_verified"}),
    "news": (m.NewsItem, {"sector_id", "headline", "summary", "why_it_matters", "link", "event_date",
                          "source_id", "last_verified"}),
}

REVIEWABLE.update({
    "lessons": (m.Lesson, {"slug", "pillar", "track", "title", "summary", "body", "level", "minutes", "language",
                           "skill_id", "position", "source_id", "last_verified"}),
    "library_items": (m.LibraryItem, {"slug", "title", "authors", "kind", "subject", "stream", "language", "publisher",
                                      "access_url", "licence_status", "licence_note", "format", "level",
                                      "edition_year", "source_id", "last_verified"}),
    "questions": (m.Question, {"slug", "pillar", "topic", "kind", "stem", "options", "correct_index", "explanation",
                               "guidance", "difficulty", "skill_id", "role_id", "sector_id", "source_id",
                               "last_verified"}),
    "assessments": (m.Assessment, {"slug", "title", "pillar", "description", "duration_minutes", "question_slugs",
                                   "credential_type", "issuer", "official_url", "source_id", "last_verified"}),
    "scenarios": (m.Scenario, {"slug", "title", "pillar", "sector_id", "difficulty", "minutes", "brief", "dimensions",
                               "nodes", "real_case", "source_id", "last_verified"}),
    "opportunities": (m.Opportunity, {"slug", "title", "organisation", "kind", "description", "eligibility", "min_year",
                                      "max_year", "streams", "skills", "location", "mode", "stipend", "duration_text",
                                      "deadline", "rolling", "selection_process", "apply_url", "sector_id",
                                      "source_id", "last_verified"}),
    "global_briefs": (m.GlobalBrief, {"slug", "category", "region", "event_date", "headline", "what_happened",
                                      "what_led", "why_matters", "who_affected", "consequences", "what_next",
                                      "investigate", "connects_to", "sector_id", "source_id", "last_verified"}),
    "countries": (m.Country, {"slug", "name", "iso_numeric", "iso_alpha3", "region", "capital", "summary", "facts",
                              "source_id", "last_verified"}),
    "timeline_events": (m.TimelineEvent, {"slug", "event_year", "title", "summary", "region", "category", "country_id",
                                          "source_id", "last_verified"}),
    "wellness_resources": (m.WellnessResource, {"slug", "title", "kind", "summary", "phone", "url", "hours",
                                                "languages", "cost", "audience", "region", "source_id",
                                                "last_verified"}),
    "practical_tools": (m.PracticalTool, {"slug", "name", "category", "what_for", "free_option", "paid_details", "url",
                                          "learn_url", "source_id", "last_verified"}),
})

# Rows that hang off a reviewable parent. parent: (parent model, fk field on this row)
LINKED: dict[str, tuple[type, set[str], tuple[type, str] | None]] = {
    "qualification_sectors": (m.QualificationSector, {"qualification_id", "sector_id", "strength", "reason",
                                                      "source_id", "last_verified"}, None),
    "role_qualifications": (m.RoleQualification, {"role_id", "qualification_id", "note"}, (m.Role, "role_id")),
    "role_requirements": (m.RoleRequirement, {"role_id", "type", "tier", "label", "note", "skill_id", "position"},
                          (m.Role, "role_id")),
    "company_roles": (m.CompanyRole, {"company_id", "role_id", "careers_url", "last_verified"},
                      (m.Company, "company_id")),
}

# publishing needs these parents to be published already
PARENTS = {
    m.Role: [(m.Sector, "sector_id")],
    m.LearningResource: [(m.Skill, "skill_id")],
    m.RoadmapStep: [(m.Qualification, "qualification_id")],
}


def _coerce(model: type, field: str, value):
    col = inspect(model).columns[field]
    if value is None:
        if not col.nullable and not (col.default is not None):
            raise HTTPException(422, f"{field} is required")
        return None
    t = col.type
    try:
        if isinstance(t, SAEnum):
            return t.enum_class(value)
        if isinstance(t, SADate):
            return value if isinstance(value, date) else date.fromisoformat(str(value))
        if isinstance(t, JSON):
            if not isinstance(value, (list, dict)):
                raise ValueError
            return value
        py = t.python_type
        if py is bool:
            if not isinstance(value, bool):
                raise ValueError
            return value
        if py is int:
            if isinstance(value, bool):
                raise ValueError
            return int(value)
        if py is str:
            s = str(value).strip()
            if getattr(t, "length", None) and len(s) > t.length:
                raise HTTPException(422, f"{field} is longer than {t.length} characters")
            return s
    except HTTPException:
        raise
    except (ValueError, TypeError, KeyError):
        raise HTTPException(422, f"{field} has an invalid value")
    return value


def _clean(model: type, allowed: set[str], data: dict, creating: bool) -> dict:
    unknown = set(data) - allowed
    if unknown:
        raise HTTPException(422, f"Unknown or read-only fields: {', '.join(sorted(unknown))}")
    out = {k: _coerce(model, k, v) for k, v in data.items()}
    for field, allowed_values in CHOICES.get(model.__tablename__, {}).items():
        if field in out and out[field] is not None and out[field] not in allowed_values:
            raise HTTPException(422, f"{field} must be one of: {', '.join(sorted(allowed_values))}")
    if creating:
        for col in inspect(model).columns:
            if col.name in allowed and not col.nullable and col.default is None and col.name not in out \
                    and not col.primary_key and col.server_default is None:
                raise HTTPException(422, f"{col.name} is required")
    return out


def audit(db: Session, user: m.User | None, action: str, etype: str, eid: int | None, detail: dict | None = None):
    db.add(m.AuditLog(user_id=user.id if user else None, action=action, entity_type=etype, entity_id=eid,
                      detail=detail))


def is_reviewer(user: m.User) -> bool:
    return user.role in (m.UserRole.reviewer, m.UserRole.admin)


def get_entry(name: str):
    if name in REVIEWABLE:
        return REVIEWABLE[name][0], REVIEWABLE[name][1], True
    if name in LINKED:
        return LINKED[name][0], LINKED[name][1], False
    raise HTTPException(404, "Unknown content type")


def create(db: Session, user: m.User, name: str, data: dict):
    model, allowed, reviewable = get_entry(name)
    clean = _clean(model, allowed, data, creating=True)
    if not reviewable:
        _check_parent_edit(db, user, name, clean)
    obj = model(**clean)
    if reviewable:
        obj.created_by_id = user.id
        obj.status = m.Status.draft
    db.add(obj)
    _flush(db)
    audit(db, user, "create", name, obj.id)
    db.commit()
    return obj


def update(db: Session, user: m.User, name: str, obj_id: int, data: dict):
    model, allowed, reviewable = get_entry(name)
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Not found")
    clean = _clean(model, allowed, data, creating=False)
    if reviewable:
        if obj.status == m.Status.published and not is_reviewer(user):
            raise HTTPException(403, "Only a reviewer can change published content")
        if obj.status == m.Status.in_review and not is_reviewer(user) and obj.created_by_id != user.id:
            raise HTTPException(403, "This item is in review")
    else:
        _check_parent_edit(db, user, name, {**{k: getattr(obj, k) for k in allowed if hasattr(obj, k)}, **clean})
    for k, v in clean.items():
        setattr(obj, k, v)
    _flush(db)
    audit(db, user, "update", name, obj.id, {"fields": sorted(clean)})
    db.commit()
    return obj


def delete(db: Session, user: m.User, name: str, obj_id: int):
    model, _allowed, reviewable = get_entry(name)
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Not found")
    if reviewable:
        if obj.status != m.Status.draft:
            raise HTTPException(409, "Only drafts can be deleted; unpublish first")
    else:
        _check_parent_edit(db, user, name, {k: getattr(obj, k, None) for k in ("role_id", "company_id")})
    db.delete(obj)
    _flush(db)
    audit(db, user, "delete", name, obj_id)
    db.commit()


def _flush(db: Session):
    from sqlalchemy.exc import IntegrityError

    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(409, "That conflicts with existing content (duplicate slug or missing reference)") from e


def _check_parent_edit(db: Session, user: m.User, name: str, values: dict):
    parent = LINKED[name][2]
    if parent is None:
        # qualification_sectors carry their own source; only reviewers change them once in use
        return
    pmodel, fk = parent
    p = db.get(pmodel, values.get(fk))
    if p is None:
        raise HTTPException(422, f"{fk} does not exist")
    if p.status == m.Status.published and not is_reviewer(user):
        raise HTTPException(403, "The parent item is published; a reviewer must make this change")


def transition(db: Session, user: m.User, name: str, obj_id: int, action: str, note: str | None = None):
    if name not in REVIEWABLE:
        raise HTTPException(404, "Unknown content type")
    model = REVIEWABLE[name][0]
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Not found")
    S = m.Status
    if action == "submit":
        if obj.status != S.draft:
            raise HTTPException(409, "Only drafts can be submitted")
        _require_provenance(obj)
        check = PUBLISH_CHECKS.get(model)
        if check:
            check(db, obj)
        obj.status = S.in_review
    elif action == "approve":
        if not is_reviewer(user):
            raise HTTPException(403, "Only a reviewer can publish")
        if obj.status != S.in_review:
            raise HTTPException(409, "Only items in review can be published")
        if obj.created_by_id == user.id and not get_settings().allow_self_review:
            raise HTTPException(403, "A different reviewer must approve your work")
        _require_provenance(obj)
        check = PUBLISH_CHECKS.get(model)
        if check:
            check(db, obj)
        for pmodel, fk in PARENTS.get(model, []):
            parent = db.get(pmodel, getattr(obj, fk))
            if parent is None or parent.status != S.published:
                raise HTTPException(409, f"Publish the linked {pmodel.__tablename__[:-1]} first")
        if model is m.Role and not obj.requirements:
            raise HTTPException(409, "Add the role's requirements before publishing")
        obj.status, obj.reviewed_by_id = S.published, user.id
        obj.reviewed_at = datetime.now(timezone.utc)
    elif action == "reject":
        if not is_reviewer(user) or obj.status != S.in_review:
            raise HTTPException(403, "Only a reviewer can send an item in review back")
        obj.status = S.draft
    elif action == "unpublish":
        if not is_reviewer(user) or obj.status != S.published:
            raise HTTPException(403, "Only a reviewer can unpublish published content")
        obj.status = S.draft
    elif action == "verify":
        if not is_reviewer(user) or obj.status != S.published:
            raise HTTPException(403, "Only a reviewer can re-verify published content")
        obj.last_verified = date.today()
    else:
        raise HTTPException(404, "Unknown action")
    audit(db, user, action, name, obj.id, {"note": note} if note else None)
    db.commit()
    return obj


def _require_provenance(obj):
    if obj.source_id is None:
        raise HTTPException(409, "Add a source before this can move forward")
    if obj.last_verified is None:
        raise HTTPException(409, "Add the date this was last verified against its source")


def stale_items(db: Session) -> list[dict]:
    cutoff = date.today() - timedelta(days=get_settings().stale_days)
    out = []
    for name, (model, _fields) in REVIEWABLE.items():
        rows = db.scalars(select(model).where(model.status == m.Status.published,
                                              (model.last_verified.is_(None)) | (model.last_verified < cutoff))).all()
        for r in rows:
            label = getattr(r, "title", None) or getattr(r, "name", None) or getattr(r, "headline", None) \
                or getattr(r, "degree", None)
            out.append({"type": name, "id": r.id, "label": label,
                        "last_verified": r.last_verified.isoformat() if r.last_verified else None})
    return out


def serialize(obj) -> dict:
    out = {}
    for col in inspect(type(obj)).columns:
        v = getattr(obj, col.name)
        if isinstance(v, enum.Enum):
            v = v.value
        elif isinstance(v, (date, datetime)):
            v = v.isoformat()
        out[col.name] = v
    return out


def _fail(msg: str):
    raise HTTPException(409, msg)


def _check_lesson(db, o):
    if len((o.body or "").strip()) < 100:
        _fail("A lesson needs a body of at least 100 characters")


def _check_library(db, o):
    if not o.access_url.startswith("https://"):
        _fail("The access link must start with https://")
    if o.licence_status not in LICENCE_STATUS:
        _fail("State the legal basis for linking this item")
    if not (o.licence_note or "").strip():
        _fail("Say in the licence note why this may be linked (for example the open-access licence or the publisher's page)")


def _check_question(db, o):
    if o.kind == "mcq":
        opts = o.options or []
        if not 2 <= len(opts) <= 6 or not all(isinstance(x, str) and x.strip() for x in opts):
            _fail("A multiple-choice question needs 2 to 6 non-empty options")
        if o.correct_index is None or not 0 <= o.correct_index < len(opts):
            _fail("Mark which option is correct")
        if not (o.explanation or "").strip():
            _fail("Explain why the answer is correct")
    else:
        if not (o.guidance or "").strip():
            _fail("An open question needs guidance on what a good answer covers")
    if not 1 <= (o.difficulty or 0) <= 3:
        _fail("Difficulty must be 1, 2 or 3")


def _check_assessment(db, o):
    slugs = list(o.question_slugs or [])
    if len(slugs) < 3 or len(set(slugs)) != len(slugs):
        _fail("An assessment needs at least 3 different questions")
    found = {q.slug: q for q in db.scalars(select(m.Question).where(m.Question.slug.in_(slugs)))}
    missing = [s for s in slugs if s not in found]
    if missing:
        _fail(f"Unknown questions: {', '.join(missing)}")
    unpublished = [s for s in slugs if found[s].status != m.Status.published]
    if unpublished:
        _fail(f"Publish these questions first: {', '.join(unpublished)}")
    if any(found[s].kind != "mcq" for s in slugs):
        _fail("Assessments can only contain multiple-choice questions, so they can be marked automatically")
    if o.credential_type != "internal" and not (o.issuer and o.official_url):
        _fail("A partner or accredited credential needs the issuer and an official link. An internal badge needs neither.")


def _check_scenario(db, o):
    from .scenario import validate

    errs = validate(o.nodes, o.dimensions)
    if errs:
        _fail("Scenario problems: " + "; ".join(errs[:5]))


def _check_opportunity(db, o):
    if not o.apply_url.startswith("https://"):
        _fail("The official application link must start with https://")
    if not o.rolling and o.deadline is None:
        _fail("Give a deadline, or mark the opportunity as rolling")


def _check_wellness(db, o):
    if o.kind == "helpline" and not (o.phone or "").strip():
        _fail("A helpline needs a phone number")
    if not (o.phone or o.url):
        _fail("Add a phone number or a link")


def _check_country(db, o):
    if not (o.iso_numeric.isdigit() and len(o.iso_numeric) == 3):
        _fail("iso_numeric must be 3 digits (for example 356 for India)")


PUBLISH_CHECKS = {m.Lesson: _check_lesson, m.LibraryItem: _check_library, m.Question: _check_question,
                  m.Assessment: _check_assessment, m.Scenario: _check_scenario,
                  m.Opportunity: _check_opportunity, m.WellnessResource: _check_wellness,
                  m.Country: _check_country}

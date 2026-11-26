"""Institutions: students choose to be counted; staff see only aggregates for groups of at least 10."""
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import admin_only, current_user

router = APIRouter(prefix="/v1", tags=["institution"])
K_MIN = 10  # no figure is shown for fewer than this many consenting students


def _hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def _new_code() -> str:
    return secrets.token_hex(5).upper()


# ---------------------------------------------------------------- admin setup
class InstitutionIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,60}$")
    kind: str = Field(default="college", max_length=30)


@router.post("/org-admin/institutions", status_code=201)
def create_institution(body: InstitutionIn, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    if db.scalar(select(m.Institution).where(m.Institution.slug == body.slug)):
        raise HTTPException(409, "That slug is taken")
    code = _new_code()
    inst = m.Institution(slug=body.slug, name=body.name, kind=body.kind, join_code_hash=_hash(code))
    db.add(inst)
    db.commit()
    return {"id": inst.id, "slug": inst.slug, "join_code": code, "note": "Shown once. Give it to students; only a hash is stored."}


@router.post("/org-admin/institutions/{inst_id}/rotate-code")
def rotate(inst_id: int, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    inst = db.get(m.Institution, inst_id)
    if inst is None:
        raise HTTPException(404, "Not found")
    code = _new_code()
    inst.join_code_hash = _hash(code)
    db.commit()
    return {"join_code": code, "note": "Shown once. The old code no longer works."}


class StaffIn(BaseModel):
    email: str
    role: str = "placement"

    @field_validator("role")
    @classmethod
    def _r(cls, v):
        if v not in ("placement", "faculty", "admin"):
            raise ValueError("role must be placement, faculty or admin")
        return v


@router.post("/org-admin/institutions/{inst_id}/staff", status_code=201)
def add_staff(inst_id: int, body: StaffIn, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    if db.get(m.Institution, inst_id) is None:
        raise HTTPException(404, "Not found")
    u = db.scalar(select(m.User).where(func.lower(m.User.email) == body.email.strip().lower()))
    if u is None:
        raise HTTPException(404, "No account with that email. Ask them to sign in once first.")
    row = db.get(m.InstitutionStaff, (u.id, inst_id)) or m.InstitutionStaff(user_id=u.id, institution_id=inst_id)
    row.role = body.role
    db.add(row)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- student side
class JoinIn(BaseModel):
    code: str = Field(min_length=4, max_length=40)
    share_readiness: bool = False
    batch_year: int | None = Field(default=None, ge=2000, le=2100)


def _membership_out(db: Session, mem: m.InstitutionMember | None) -> dict | None:
    if mem is None:
        return None
    inst = db.get(m.Institution, mem.institution_id)
    return {"institution": inst.name, "slug": inst.slug, "share_readiness": mem.share_readiness, "batch_year": mem.batch_year,
            "what_is_shared": "If you switch sharing on, your institution sees only totals for groups of 10 or more students: for example how many have built a profile. "
                              "They never see your name, answers, wellness journal or individual scores."}


@router.get("/me/institution")
def my_institution(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mem = db.scalar(select(m.InstitutionMember).where(m.InstitutionMember.user_id == user.id))
    return _membership_out(db, mem)


@router.post("/me/institution/join")
def join(body: JoinIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    h = _hash(body.code)
    inst = next((i for i in db.scalars(select(m.Institution)) if hmac.compare_digest(i.join_code_hash, h)), None)
    if inst is None:
        raise HTTPException(404, "That code was not recognised")
    db.query(m.InstitutionMember).filter(m.InstitutionMember.user_id == user.id).delete()
    mem = m.InstitutionMember(user_id=user.id, institution_id=inst.id, share_readiness=body.share_readiness, batch_year=body.batch_year)
    db.add(mem)
    db.commit()
    return _membership_out(db, mem)


class ConsentIn(BaseModel):
    share_readiness: bool
    batch_year: int | None = Field(default=None, ge=2000, le=2100)


@router.put("/me/institution")
def consent(body: ConsentIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mem = db.scalar(select(m.InstitutionMember).where(m.InstitutionMember.user_id == user.id))
    if mem is None:
        raise HTTPException(404, "You have not joined an institution")
    mem.share_readiness, mem.batch_year = body.share_readiness, body.batch_year
    db.commit()
    return _membership_out(db, mem)


@router.delete("/me/institution", status_code=204)
def leave(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(m.InstitutionMember).filter(m.InstitutionMember.user_id == user.id).delete()
    db.commit()


# ---------------------------------------------------------------- staff aggregates
@router.get("/institution/{slug}/overview")
def overview(slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    inst = db.scalar(select(m.Institution).where(m.Institution.slug == slug))
    staff = inst and db.get(m.InstitutionStaff, (user.id, inst.id))
    if inst is None or staff is None:
        raise HTTPException(404, "Not found")
    ids = list(db.scalars(select(m.InstitutionMember.user_id).where(
        m.InstitutionMember.institution_id == inst.id, m.InstitutionMember.share_readiness.is_(True))))
    n = len(ids)
    out = {"institution": inst.name, "sharing_students": n, "minimum_group": K_MIN,
           "privacy": "Only students who switched sharing on are counted. Figures appear only for groups of 10 or more. Wellness data is never included."}
    if n < K_MIN:
        out["suppressed"] = True
        out["message"] = f"Fewer than {K_MIN} students are sharing, so no figures are shown."
        return out

    def distinct(model, col=None):
        c = col if col is not None else model.user_id
        return db.scalar(select(func.count(func.distinct(c))).where(c.in_(ids))) or 0

    def pct(x: int) -> float:
        return round(100 * x / n)

    out |= {
        "has_profile": pct(distinct(m.MasterEntry)),
        "has_resume": pct(distinct(m.Resume)),
        "practised_interview_questions": pct(distinct(m.DefenceAnswer)),
        "practised_questions": pct(distinct(m.QuestionResponse)),
        "tracking_applications": pct(distinct(m.Application)),
        "unit": "percent of sharing students",
        "suppressed": False,
    }
    # placement-cell and faculty views: every line is a group of at least K_MIN sharing students, never one person
    out["assessments_completed"] = pct(distinct(m.AssessmentAttempt, m.AssessmentAttempt.user_id))
    out["completed_scenarios"] = pct(db.scalar(select(func.count(func.distinct(m.ScenarioRun.user_id))).where(
        m.ScenarioRun.user_id.in_(ids), m.ScenarioRun.completed.is_(True))) or 0)
    stages = {}
    for st, c in db.execute(select(m.Application.status, func.count(func.distinct(m.Application.user_id))).where(
            m.Application.user_id.in_(ids)).group_by(m.Application.status)):
        if c >= K_MIN:
            stages[st] = c
    out["application_stages_students"] = stages
    skills: dict[str, set] = {}
    for uid, title in db.execute(select(m.MasterEntry.user_id, m.MasterEntry.title).where(
            m.MasterEntry.user_id.in_(ids), m.MasterEntry.section == "skill")):
        skills.setdefault(title.strip().lower(), set()).add(uid)
    out["common_skills"] = sorted(({"skill": k, "students": len(v)} for k, v in skills.items() if len(v) >= K_MIN), key=lambda x: -x["students"])[:15]
    topics: dict[tuple, list] = {}
    for uid, pillar, topic, att, cor in db.execute(select(m.TopicProgress.user_id, m.TopicProgress.pillar, m.TopicProgress.topic,
                                                          m.TopicProgress.attempts, m.TopicProgress.correct).where(
            m.TopicProgress.user_id.in_(ids), m.TopicProgress.attempts > 0)):
        topics.setdefault((pillar, topic), []).append(cor / att)
    gaps = [{"pillar": k[0], "topic": k[1], "students": len(v), "average_accuracy": round(100 * sum(v) / len(v))}
            for k, v in topics.items() if len(v) >= K_MIN]
    out["learning_gaps"] = sorted(gaps, key=lambda x: x["average_accuracy"])[:10]
    out["gap_note"] = "Topics where sharing students, on average, answer fewer questions correctly. For planning teaching, not for judging individuals."
    # per-batch breakdown only where each batch is itself large enough
    by = {}
    for y, c in db.execute(select(m.InstitutionMember.batch_year, func.count()).where(m.InstitutionMember.user_id.in_(ids)).group_by(m.InstitutionMember.batch_year)):
        if y is not None and c >= K_MIN:
            by[str(y)] = c
    out["batches"] = by
    return out

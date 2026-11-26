"""Signed-in routes: master profile, resumes, defence practice, personal branding and the public portfolio."""
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .. import meta
from .. import models as m
from ..db import get_db
from ..deps import current_user
from ..services import badges, resume as rs

router = APIRouter(prefix="/v1/me", tags=["me-build"])
public_router = APIRouter(prefix="/v1/portfolios", tags=["portfolio"])
PUB = m.Status.published


def _own(db: Session, model, obj_id: int, user: m.User):
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(404, "Not found")
    return obj


# ---------------------------------------------------------------- master profile
class Evidence(BaseModel):
    kind: str
    url: str = Field(max_length=2048)
    label: str | None = Field(default=None, max_length=120)

    @field_validator("kind")
    @classmethod
    def _k(cls, v):
        if v not in meta.EVIDENCE_KINDS:
            raise ValueError("kind must be one of: " + ", ".join(sorted(meta.EVIDENCE_KINDS)))
        return v

    @field_validator("url")
    @classmethod
    def _u(cls, v):
        if not v.startswith("https://"):
            raise ValueError("links must start with https://")
        return v


class EntryIn(BaseModel):
    section: str
    title: str = Field(min_length=1, max_length=200)
    organisation: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    current: bool = False
    detail: str | None = Field(default=None, max_length=300)
    bullets: list[str] = Field(default_factory=list, max_length=8)
    evidence: list[Evidence] = Field(default_factory=list, max_length=5)
    tags: list[str] = Field(default_factory=list, max_length=10)
    position: int = Field(default=0, ge=0, le=1000)

    @field_validator("section")
    @classmethod
    def _s(cls, v):
        if v not in meta.MASTER_SECTIONS:
            raise ValueError("section must be one of: " + ", ".join(meta.MASTER_SECTIONS))
        return v

    @field_validator("bullets")
    @classmethod
    def _b(cls, v):
        v = [b.strip() for b in v if b.strip()]
        if any(len(b) > 400 for b in v):
            raise ValueError("each bullet must be 400 characters or fewer")
        return v

    @field_validator("tags")
    @classmethod
    def _t(cls, v):
        v = list(dict.fromkeys(t.strip() for t in v if t.strip()))
        if any(len(t) > 40 for t in v):
            raise ValueError("each tag must be 40 characters or fewer")
        return v


def _entry_out(e: m.MasterEntry, demo: dict | None = None) -> dict:
    d = {"id": e.id, "section": e.section, "title": e.title, "organisation": e.organisation, "location": e.location,
         "start_date": e.start_date.isoformat() if e.start_date else None, "end_date": e.end_date.isoformat() if e.end_date else None,
         "current": e.current, "detail": e.detail, "bullets": e.bullets, "evidence": e.evidence, "tags": e.tags, "position": e.position}
    if e.section == "skill" and demo is not None:
        d["basis"] = "demonstrated" if demo.get(e.id) else "self-reported"
    return d


def _entries(db: Session, user: m.User) -> list[m.MasterEntry]:
    return list(db.scalars(select(m.MasterEntry).where(m.MasterEntry.user_id == user.id).order_by(m.MasterEntry.position, m.MasterEntry.id)))


@router.get("/master")
def master(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    es = _entries(db, user)
    demo = rs.demonstrated(es)
    return {"sections": meta.MASTER_SECTIONS, "labels": rs.SECTION_LABEL, "entries": [_entry_out(e, demo) for e in es],
            "note": "Your master profile is the single source for every resume. Only add what is true; you will be asked about it."}


def _validate_entry(body: EntryIn):
    if body.start_date and body.end_date and body.end_date < body.start_date:
        raise HTTPException(422, "The end date is before the start date")


@router.post("/master", status_code=201)
def add_entry(body: EntryIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _validate_entry(body)
    if (db.scalar(select(func.count()).select_from(m.MasterEntry).where(m.MasterEntry.user_id == user.id)) or 0) >= 300:
        raise HTTPException(409, "You have reached the limit of 300 entries.")
    e = m.MasterEntry(user_id=user.id, **{**body.model_dump(), "evidence": [x.model_dump() for x in body.evidence]})
    db.add(e)
    db.flush()
    badges.touch(db, user.id)
    db.commit()
    return _entry_out(e)


@router.put("/master/{entry_id}")
def edit_entry(entry_id: int, body: EntryIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _validate_entry(body)
    e = _own(db, m.MasterEntry, entry_id, user)
    for k, v in {**body.model_dump(), "evidence": [x.model_dump() for x in body.evidence]}.items():
        setattr(e, k, v)
    badges.touch(db, user.id)
    db.commit()
    return _entry_out(e)


@router.delete("/master/{entry_id}", status_code=204)
def delete_entry(entry_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.MasterEntry, entry_id, user))
    db.commit()


# ---------------------------------------------------------------- resumes
class Contact(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=120)
    links: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("links")
    @classmethod
    def _l(cls, v):
        if any(not x.startswith("https://") or len(x) > 300 for x in v):
            raise ValueError("links must start with https://")
        return v


class Selection(BaseModel):
    entry_id: int
    bullets: list[int] | None = None


class ResumeIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target_kind: str = "general"
    target_ref: str | None = Field(default=None, max_length=160)
    job_description: str | None = Field(default=None, max_length=8000)
    headline: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=1200)
    contact: Contact = Field(default_factory=Contact)
    selection: list[Selection] = Field(default_factory=list, max_length=300)
    section_order: list[str] = Field(default_factory=list, max_length=20)
    change_note: str | None = Field(default=None, max_length=200)

    @field_validator("target_kind")
    @classmethod
    def _k(cls, v):
        if v not in meta.RESUME_TARGETS:
            raise ValueError("target_kind must be one of: " + ", ".join(sorted(meta.RESUME_TARGETS)))
        return v

    @field_validator("section_order")
    @classmethod
    def _o(cls, v):
        if any(s not in meta.MASTER_SECTIONS for s in v):
            raise ValueError("unknown section in section_order")
        return v


def _resume_out(r: m.Resume) -> dict:
    return {"id": r.id, "name": r.name, "target_kind": r.target_kind, "target_ref": r.target_ref, "job_description": r.job_description,
            "headline": r.headline, "summary": r.summary, "contact": r.contact, "selection": r.selection,
            "section_order": r.section_order, "updated_at": r.updated_at.isoformat()}


def _snapshot(r: m.Resume) -> dict:
    return {k: v for k, v in _resume_out(r).items() if k not in ("id", "updated_at")}


def _apply(db: Session, user: m.User, r: m.Resume, body: ResumeIn):
    ids = {e.id for e in _entries(db, user)}
    for s in body.selection:
        if s.entry_id not in ids:
            raise HTTPException(422, "A selected entry does not exist in your master profile")
    r.name, r.target_kind, r.target_ref = body.name, body.target_kind, body.target_ref
    r.job_description, r.headline, r.summary = body.job_description, body.headline, body.summary
    r.contact = body.contact.model_dump()
    r.selection = [s.model_dump() for s in body.selection]
    r.section_order = body.section_order


def _save_version(db: Session, r: m.Resume, note: str | None, previous: dict | None):
    snap = _snapshot(r)
    if previous is not None and previous == snap:
        return
    if not note:
        note = "First version" if previous is None else _diff_note(previous, snap)
    db.add(m.ResumeVersion(resume_id=r.id, snapshot=snap, change_note=note))
    db.flush()
    keep = [v.id for v in db.scalars(select(m.ResumeVersion).where(m.ResumeVersion.resume_id == r.id).order_by(m.ResumeVersion.id.desc()))]
    for old in keep[30:]:
        db.delete(db.get(m.ResumeVersion, old))


def _diff_note(a: dict, b: dict) -> str:
    changes = [k.replace("_", " ") for k in ("name", "headline", "summary", "job_description", "target_kind", "target_ref", "contact", "section_order")
               if a.get(k) != b.get(k)]
    before, after = {s["entry_id"] for s in a.get("selection", [])}, {s["entry_id"] for s in b.get("selection", [])}
    if after - before:
        changes.append(f"{len(after - before)} entries added")
    if before - after:
        changes.append(f"{len(before - after)} entries removed")
    if a.get("selection") != b.get("selection") and not (after - before or before - after):
        changes.append("bullet choices")
    return "Changed " + ", ".join(changes) if changes else "Edited"


@router.get("/resumes")
def resumes(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return [_resume_out(r) for r in db.scalars(select(m.Resume).where(m.Resume.user_id == user.id).order_by(m.Resume.updated_at.desc()))]


@router.post("/resumes", status_code=201)
def new_resume(body: ResumeIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if (db.scalar(select(func.count()).select_from(m.Resume).where(m.Resume.user_id == user.id)) or 0) >= 50:
        raise HTTPException(409, "You have reached the limit of 50 resumes.")
    r = m.Resume(user_id=user.id)
    _apply(db, user, r, body)
    db.add(r)
    db.flush()
    _save_version(db, r, body.change_note, None)
    badges.touch(db, user.id)
    db.commit()
    return _resume_out(r)


class CompanyCopyIn(BaseModel):
    company_slug: str = Field(min_length=1, max_length=120)
    job_description: str | None = Field(default=None, max_length=8000)


@router.post("/resumes/{resume_id}/company-copy", status_code=201)
def company_copy(resume_id: int, body: CompanyCopyIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """A copy of this resume aimed at one company. Same entries, so nothing new is claimed; edit the copy freely."""
    src = _load(db, user, resume_id)
    co = db.scalar(select(m.Company).where(m.Company.slug == body.company_slug, m.Company.status == PUB))
    if co is None:
        raise HTTPException(404, "That company is not published")
    if (db.scalar(select(func.count()).select_from(m.Resume).where(m.Resume.user_id == user.id)) or 0) >= 50:
        raise HTTPException(409, "You have reached the limit of 50 resumes.")
    data = {**_snapshot(src), "name": f"{src.name} for {co.name}"[:160], "target_kind": "company", "target_ref": co.slug,
            "job_description": body.job_description if body.job_description is not None else src.job_description,
            "change_note": f"Copied from '{src.name}' for {co.name}"}
    r = m.Resume(user_id=user.id)
    _apply(db, user, r, ResumeIn(**data))
    db.add(r)
    db.flush()
    _save_version(db, r, data["change_note"], None)
    db.commit()
    return _resume_out(r)


def _load(db: Session, user: m.User, resume_id: int) -> m.Resume:
    return _own(db, m.Resume, resume_id, user)


@router.get("/resumes/{resume_id}")
def get_resume(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return _resume_out(_load(db, user, resume_id))


@router.put("/resumes/{resume_id}")
def edit_resume(resume_id: int, body: ResumeIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    before = _snapshot(r)
    _apply(db, user, r, body)
    db.flush()
    _save_version(db, r, body.change_note, before)
    db.commit()
    return _resume_out(r)


@router.delete("/resumes/{resume_id}", status_code=204)
def delete_resume(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_load(db, user, resume_id))
    db.commit()


@router.get("/resumes/{resume_id}/versions")
def versions(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    return [{"id": v.id, "note": v.change_note, "created_at": v.created_at.isoformat()} for v in r.versions]


@router.post("/resumes/{resume_id}/restore/{version_id}")
def restore(resume_id: int, version_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    v = db.get(m.ResumeVersion, version_id)
    if v is None or v.resume_id != r.id:
        raise HTTPException(404, "Not found")
    before = _snapshot(r)
    snap = v.snapshot
    ids = {e.id for e in _entries(db, user)}
    r.name, r.target_kind, r.target_ref = snap["name"], snap["target_kind"], snap.get("target_ref")
    r.job_description, r.headline, r.summary = snap.get("job_description"), snap.get("headline"), snap.get("summary")
    r.contact, r.section_order = snap.get("contact") or {}, snap.get("section_order") or []
    r.selection = [s for s in snap.get("selection", []) if s["entry_id"] in ids]
    db.flush()
    _save_version(db, r, f"Restored an earlier version ({v.created_at.date().isoformat()})", before)
    db.commit()
    return _resume_out(r)


def _assembled(db: Session, user: m.User, r: m.Resume):
    es = _entries(db, user)
    return rs.assemble(r, es), es


def _role_terms(db: Session, r: m.Resume) -> list[str] | None:
    if r.target_kind == "role" and r.target_ref:
        role = db.scalar(select(m.Role).where(m.Role.slug == r.target_ref, m.Role.status == PUB).options(selectinload(m.Role.requirements)))
        if role:
            return [q.label for q in role.requirements] + [role.title]
    if r.target_kind == "sector" and r.target_ref:
        sec = db.scalar(select(m.Sector).where(m.Sector.slug == r.target_ref, m.Sector.status == PUB))
        if sec:
            return [sec.name]
    return None


@router.get("/resumes/{resume_id}/preview")
def preview(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    doc, _ = _assembled(db, user, r)
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in _jsonable(doc).items()}


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_jsonable(x) for x in o]
    if isinstance(o, date):
        return o.isoformat()
    return o


@router.get("/resumes/{resume_id}/check")
def check(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    doc, es = _assembled(db, user, r)
    return rs.check(doc, es, r.job_description, _role_terms(db, r))


@router.get("/resumes/{resume_id}/gaps")
def gaps(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    out = rs.gap_analysis(_entries(db, user), r.job_description, _role_terms(db, r))
    todo = [i["term"] for i in out["items"] if i["state"] in ("to_acquire", "claimed")]
    skills = db.scalars(select(m.Skill).where(m.Skill.status == PUB)).all() if todo else []
    learn = [{"term": t, "skill": s.slug, "name": s.name} for t in todo for s in skills if t in s.name.lower()][:12]
    return {**out, "learn": learn}


@router.post("/resumes/{resume_id}/suggest")
def suggest(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    es = _entries(db, user)
    sel = rs.suggest_selection(es, r.job_description, _role_terms(db, r))
    titles = {e.id: e.title for e in es}
    return {"selection": sel, "titles": [titles[s["entry_id"]] for s in sel],
            "note": "A suggestion based on word overlap. You decide what goes on your resume, and every line must be true."}


@router.get("/resumes/{resume_id}/export.docx")
def export_docx(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    doc, _ = _assembled(db, user, r)
    return Response(rs.to_docx(_jsonable_dates(doc)), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="{_fname(r.name)}.docx"'})


@router.get("/resumes/{resume_id}/export.pdf")
def export_pdf(resume_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    doc, _ = _assembled(db, user, r)
    return Response(rs.to_pdf(_jsonable_dates(doc)), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{_fname(r.name)}.pdf"'})


def _jsonable_dates(doc):
    return doc  # exports read the already formatted "dates" text, not the date objects


def _fname(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-")[:60] or "resume"


# ---------------------------------------------------------------- resume defence
class DefenceIn(BaseModel):
    resume_id: int | None = None
    entry_id: int | None = None
    topic: str = Field(max_length=60)
    question: str = Field(min_length=3, max_length=1500)
    answer: str = Field(min_length=1, max_length=4000)
    self_scores: dict[str, int] = Field(default_factory=dict)


@router.get("/resumes/{resume_id}/defence")
def defence_questions(resume_id: int, level: int = Query(5, ge=1, le=5), mode: str = Query("practice", pattern="^(study|practice|simulation)$"),
                      user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = _load(db, user, resume_id)
    es = _entries(db, user)
    chosen = {s["entry_id"] for s in r.selection} if r.selection else {e.id for e in es}
    qs = [q for q in rs.defence_questions([e for e in es if e.id in chosen]) if q["level"] <= level]
    if mode != "study":
        for q in qs:
            q.pop("hint", None)
    return {"questions": qs, "level": level, "mode": mode, "levels": rs.LEVELS_TEXT, "time_limit_seconds": 120 if mode == "simulation" else None, "note": "Every question comes from something you wrote. If you cannot answer it honestly, fix the resume, not the answer."}


@router.post("/defence/answers", status_code=201)
def defence_answer(body: DefenceIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    scores = {k: v for k, v in body.self_scores.items() if k in ("clarity", "depth", "honesty", "confidence") and 1 <= v <= 5}
    if body.resume_id is not None:
        _load(db, user, body.resume_id)
    fb = rs.answer_feedback(body.answer)
    row = m.DefenceAnswer(user_id=user.id, resume_id=body.resume_id, entry_id=body.entry_id, topic=body.topic,
                          question=body.question, answer=body.answer, self_scores=scores, feedback=fb)
    db.add(row)
    new = badges.touch(db, user.id)
    db.commit()
    return {"id": row.id, "automatic_checks": fb, "new_badges": new, **rs.answer_dimensions(body.answer, body.question),
            "note": "Automatic checks look at structure only. They cannot tell whether your answer is true or good."}


@router.get("/defence/readiness")
def readiness(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = list(db.scalars(select(m.DefenceAnswer).where(m.DefenceAnswer.user_id == user.id).order_by(m.DefenceAnswer.id.desc()).limit(500)))
    topics: dict[str, list[float]] = {}
    mistakes: dict[str, int] = {}
    for r in rows:
        if r.self_scores:
            topics.setdefault(r.topic, []).append(sum(r.self_scores.values()) / len(r.self_scores))
        for f in r.feedback or []:
            mistakes[f["kind"]] = mistakes.get(f["kind"], 0) + 1
    open_n = db.scalar(select(func.count()).select_from(m.QuestionResponse).where(
        m.QuestionResponse.user_id == user.id, m.QuestionResponse.answer_text.is_not(None))) or 0
    weak = sorted(({"topic": t, "average_self_rating": round(sum(v) / len(v), 1), "answers": len(v)} for t, v in topics.items()),
                  key=lambda x: x["average_self_rating"])
    return {"answers_practised": len(rows), "open_questions_practised": open_n, "topics": weak[:12],
            "repeated_feedback": sorted(({"kind": k, "times": n} for k, n in mistakes.items() if n >= 2), key=lambda x: -x["times"]),
            "history": [{"id": r.id, "topic": r.topic, "question": r.question, "date": r.created_at.date().isoformat()} for r in rows[:20]],
            "note": "Self-ratings are yours. Use them to decide what to practise next, not as a score."}


# ---------------------------------------------------------------- branding and portfolio
@router.get("/branding")
def branding(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    es = _entries(db, user)
    by: dict[str, list[m.MasterEntry]] = {}
    for e in es:
        by.setdefault(e.section, []).append(e)
    edu = (by.get("education") or [None])[0]
    proj = (by.get("project") or [None])[0]
    skills = [e.title for e in by.get("skill", [])][:4]
    parts = []
    if edu:
        parts.append(f"I'm studying {edu.title}" + (f" at {edu.organisation}" if edu.organisation else "") + ".")
    if proj:
        parts.append(f"Recently I worked on {proj.title}" + (f", where I {proj.bullets[0][0].lower() + proj.bullets[0][1:]}" if proj.bullets else "") + ".")
    if skills:
        parts.append("I'm building skills in " + ", ".join(skills[:-1]) + (" and " if len(skills) > 1 else "") + skills[-1] + ".")
    ev = [x for e in es for x in (e.evidence or [])]
    kinds = {x.get("kind") for x in ev}
    checklist = [
        {"item": "Add at least one project with a link to the real work (code, document, design)", "done": "github" in kinds or "portfolio" in kinds},
        {"item": "Attach evidence to your certifications (certificate link or verification page)", "done": "certificate" in kinds},
        {"item": "Have a one-line headline that says what you do, not just what you study", "done": False},
        {"item": "Use the same name and a clear photo-free summary across your resume, LinkedIn and GitHub", "done": False},
        {"item": "On GitHub, pin your best repositories and give each a README that says what it does and how to run it", "done": "github" in kinds},
        {"item": "On LinkedIn, make the headline and About section match the role you are aiming for", "done": False},
    ]
    return {"introduction_draft": " ".join(parts) if parts else None,
            "note": "This draft is assembled only from what you entered. Rewrite it in your own voice before you use it.",
            "checklist": checklist}


class PortfolioIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,40}$")
    enabled: bool = False
    indexable: bool = False
    display_name: str = Field(min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)
    entry_ids: list[int] = Field(default_factory=list, max_length=100)
    links: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("links")
    @classmethod
    def _l(cls, v):
        if any(not x.startswith("https://") or len(x) > 300 for x in v):
            raise ValueError("links must start with https://")
        return v


def _portfolio_out(p: m.Portfolio) -> dict:
    return {"slug": p.slug, "enabled": p.enabled, "indexable": p.indexable, "display_name": p.display_name, "headline": p.headline,
            "bio": p.bio, "entry_ids": p.entry_ids, "links": p.links}


@router.get("/portfolio")
def get_portfolio(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(m.Portfolio, user.id)
    return _portfolio_out(p) if p else None


@router.put("/portfolio")
def put_portfolio(body: PortfolioIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    ids = {e.id for e in _entries(db, user)}
    if any(i not in ids for i in body.entry_ids):
        raise HTTPException(422, "An entry does not exist in your master profile")
    taken = db.scalar(select(m.Portfolio).where(m.Portfolio.slug == body.slug, m.Portfolio.user_id != user.id))
    if taken:
        raise HTTPException(409, "That web address is taken")
    p = db.get(m.Portfolio, user.id) or m.Portfolio(user_id=user.id)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.add(p)
    db.commit()
    return _portfolio_out(p)


@router.delete("/portfolio", status_code=204)
def delete_portfolio(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(m.Portfolio, user.id)
    if p:
        db.delete(p)
        db.commit()


@public_router.get("/{slug}")
def public_portfolio(slug: str, db: Session = Depends(get_db)):
    p = db.scalar(select(m.Portfolio).where(m.Portfolio.slug == slug, m.Portfolio.enabled.is_(True)))
    if p is None:
        raise HTTPException(404, "Not found")
    es = {e.id: e for e in db.scalars(select(m.MasterEntry).where(m.MasterEntry.user_id == p.user_id, m.MasterEntry.id.in_(p.entry_ids or [])))}
    items = []
    for i in p.entry_ids:
        e = es.get(i)
        if e:
            items.append({"section": e.section, "title": e.title, "organisation": e.organisation, "dates": rs._fmt_dates(rs.entry_dict(e)),
                          "detail": e.detail, "bullets": e.bullets, "evidence": e.evidence, "tags": e.tags})
    return {"display_name": p.display_name, "headline": p.headline, "bio": p.bio, "links": p.links, "indexable": p.indexable,
            "entries": items, "note": "Published by the student. Samarthya has not verified these claims."}

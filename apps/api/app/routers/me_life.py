"""Signed-in routes: applications and opportunity matching, and the private wellness journal."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .. import meta
from .. import models as m
from ..db import get_db
from ..deps import current_user
from ..routers.content import _opp_out, open_opportunities
from ..services import badges
from ..services.crypto import decrypt, encrypt
from ..services.safety import CRISIS_RESOURCES, crisis_signal

router = APIRouter(prefix="/v1/me", tags=["me-life"])
PUB = m.Status.published
FINAL = {"rejected", "withdrawn", "offer"}


def _own(db: Session, model, obj_id: int, user: m.User):
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(404, "Not found")
    return obj


# ---------------------------------------------------------------- applications
class ApplicationIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    organisation: str | None = Field(default=None, max_length=200)
    apply_url: str | None = Field(default=None, max_length=2048)
    status: str = "saved"
    resume_id: int | None = None
    deadline: date | None = None
    follow_up: date | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        if v not in meta.APPLICATION_STATUS:
            raise ValueError("status must be one of: " + ", ".join(meta.APPLICATION_STATUS))
        return v

    @field_validator("apply_url")
    @classmethod
    def _u(cls, v):
        if v and not v.startswith("https://"):
            raise ValueError("the link must start with https://")
        return v


def _app(a: m.Application) -> dict:
    return {"id": a.id, "title": a.title, "organisation": a.organisation, "apply_url": a.apply_url, "status": a.status,
            "resume_id": a.resume_id, "deadline": a.deadline.isoformat() if a.deadline else None,
            "follow_up": a.follow_up.isoformat() if a.follow_up else None, "notes": a.notes, "history": a.history,
            "opportunity": a.opportunity.slug if a.opportunity else None}


def _resume_ok(db: Session, user: m.User, rid: int | None):
    if rid is not None:
        _own(db, m.Resume, rid, user)


@router.get("/applications")
def applications(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Application).where(m.Application.user_id == user.id).order_by(
        m.Application.deadline.asc().nullslast(), m.Application.id.desc()).limit(500)).all()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {"items": [_app(r) for r in rows], "counts": counts, "statuses": meta.APPLICATION_STATUS}


@router.post("/applications", status_code=201)
def add_application(body: ApplicationIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if (db.scalar(select(func.count()).select_from(m.Application).where(m.Application.user_id == user.id)) or 0) >= 1000:
        raise HTTPException(409, "You have reached the limit of 1000 tracked applications.")
    _resume_ok(db, user, body.resume_id)
    a = m.Application(user_id=user.id, **body.model_dump(), history=[{"status": body.status, "date": date.today().isoformat()}])
    db.add(a)
    badges.touch(db, user.id)
    db.commit()
    return _app(a)


@router.post("/applications/from-opportunity/{slug}", status_code=201)
def from_opportunity(slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    o = db.scalar(select(m.Opportunity).where(m.Opportunity.slug == slug, open_opportunities()))
    if o is None:
        raise HTTPException(404, "That opportunity is not open or does not exist")
    exists = db.scalar(select(m.Application).where(m.Application.user_id == user.id, m.Application.opportunity_id == o.id))
    if exists:
        return _app(exists)
    a = m.Application(user_id=user.id, opportunity_id=o.id, title=o.title, organisation=o.organisation, apply_url=o.apply_url,
                      deadline=o.deadline, status="saved", history=[{"status": "saved", "date": date.today().isoformat()}])
    db.add(a)
    badges.touch(db, user.id)
    db.commit()
    return _app(a)


@router.put("/applications/{app_id}")
def edit_application(app_id: int, body: ApplicationIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    a = _own(db, m.Application, app_id, user)
    _resume_ok(db, user, body.resume_id)
    if body.status != a.status:
        a.history = list(a.history or []) + [{"status": body.status, "date": date.today().isoformat()}]
    for k, v in body.model_dump().items():
        setattr(a, k, v)
    db.commit()
    return _app(a)


@router.delete("/applications/{app_id}", status_code=204)
def delete_application(app_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.Application, app_id, user))
    db.commit()


@router.get("/applications/reminders")
def reminders(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    today = date.today()
    out = []
    for a in db.scalars(select(m.Application).where(m.Application.user_id == user.id, m.Application.status.notin_(FINAL))):
        if a.deadline and a.status in ("saved", "preparing") and today <= a.deadline <= today + timedelta(days=7):
            out.append({"id": a.id, "title": a.title, "kind": "deadline", "date": a.deadline.isoformat(),
                        "days_left": (a.deadline - today).days})
        elif a.deadline and a.status in ("saved", "preparing") and a.deadline < today:
            out.append({"id": a.id, "title": a.title, "kind": "missed", "date": a.deadline.isoformat(), "days_left": (a.deadline - today).days})
        if a.follow_up and a.follow_up <= today + timedelta(days=3):
            out.append({"id": a.id, "title": a.title, "kind": "follow_up", "date": a.follow_up.isoformat(), "days_left": (a.follow_up - today).days})
    return sorted(out, key=lambda r: r["date"])


@router.get("/applications.ics")
def applications_ics(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Samarthya//Applications//EN", "CALSCALE:GREGORIAN"]

    def esc(t: str) -> str:
        return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", " ")

    for a in db.scalars(select(m.Application).where(m.Application.user_id == user.id, m.Application.status.notin_(FINAL))):
        for d, label in ((a.deadline, "Deadline"), (a.follow_up, "Follow up")):
            if d:
                lines += ["BEGIN:VEVENT", f"UID:app-{a.id}-{label.replace(' ', '').lower()}@samarthya", f"DTSTAMP:{datetime.utcnow():%Y%m%dT%H%M%SZ}",
                          f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
                          f"SUMMARY:{esc(label + ': ' + a.title)}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", media_type="text/calendar",
                    headers={"Content-Disposition": 'attachment; filename="samarthya-applications.ics"'})


@router.get("/opportunities/matches")
def matches(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    prof = db.get(m.Profile, user.id)
    qual = db.get(m.Qualification, prof.qualification_id) if prof and prof.qualification_id else None
    year, skills = (prof.year_of_study if prof else None), set(prof.skills if prof else [])
    interest_sectors = set()
    if prof and prof.interests:
        interest_sectors = set(db.scalars(select(m.Sector.id).where(m.Sector.slug.in_(prof.interests))))
    good, partial = [], []
    for o in db.scalars(select(m.Opportunity).where(open_opportunities()).order_by(m.Opportunity.deadline.asc().nullslast()).limit(400)):
        reasons, blockers, unknown = [], [], []
        if o.min_year or o.max_year:
            if year is None:
                unknown.append("Add your year of study to check the year requirement")
            elif (o.min_year and year < o.min_year) or (o.max_year and year > o.max_year):
                blockers.append(f"Listed for year {o.min_year or 1}" + (f" to {o.max_year}" if o.max_year else "") + f"; you are in year {year}")
            else:
                reasons.append("Your year of study fits")
        if o.streams:
            if qual is None or not qual.stream:
                unknown.append("Add your degree to check the stream requirement")
            elif qual.stream in o.streams:
                reasons.append(f"Open to {qual.stream}")
            else:
                blockers.append("Listed for " + ", ".join(o.streams))
        sk = skills & set(o.skills or [])
        if sk:
            reasons.append("You listed " + ", ".join(sorted(sk)))
        if o.sector_id in interest_sectors:
            reasons.append("In a sector you are interested in")
        item = _opp_out(o, full=False) | {"reasons": reasons, "to_check": unknown, "blockers": blockers}
        if blockers:
            if reasons:
                partial.append(item)
        elif reasons:
            good.append(item)
    return {"matches": good[:30], "worth_a_look": partial[:15],
            "note": "Matching uses only what you told us. It is a starting point; read the official eligibility before applying."}


# ---------------------------------------------------------------- wellness journal
PROMPTS = [
    "What is taking up most of your attention today? Write it down without fixing it.",
    "Name one thing that felt a little easier than last week.",
    "What do you need more of right now: rest, company, quiet, or help with something practical?",
    "If a friend described your week to you, what would you say to them?",
    "What is one small thing you can do in the next hour that would be kind to yourself?",
    "What are you worried about that you cannot control, and what part is yours to act on?",
    "Who is someone you could tell how you are really doing?",
]


class JournalIn(BaseModel):
    day: date | None = None
    mood: int | None = Field(default=None, ge=1, le=5)
    body: str = Field(default="", max_length=5000)


@router.get("/journal")
def journal(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.JournalEntry).where(m.JournalEntry.user_id == user.id).order_by(m.JournalEntry.day.desc(), m.JournalEntry.id.desc()).limit(365))
    return {"entries": [{"id": r.id, "day": r.day.isoformat(), "mood": r.mood, "body": decrypt(r.body_enc) if r.body_enc else ""} for r in rows],
            "privacy": "Only you can read these. The text is encrypted in storage, never shared with institutions or employers, and not used for badges or streaks."}


@router.post("/journal", status_code=201)
def add_journal(body: JournalIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if not body.body.strip() and body.mood is None:
        raise HTTPException(422, "Write something or choose a mood")
    day = body.day or date.today()
    if day > date.today():
        raise HTTPException(422, "The date cannot be in the future")
    if (db.scalar(select(func.count()).select_from(m.JournalEntry).where(m.JournalEntry.user_id == user.id)) or 0) >= 3000:
        raise HTTPException(409, "You have reached the limit of 3000 entries.")
    row = m.JournalEntry(user_id=user.id, day=day, mood=body.mood, body_enc=encrypt(body.body) if body.body.strip() else "")
    db.add(row)
    db.commit()
    out = {"id": row.id}
    if crisis_signal(body.body):
        out |= {"crisis": True, "message": "What you wrote sounds really painful. You do not have to carry it alone. "
                "Please reach out to someone now. These services are free and confidential, and if you are in immediate danger call 112.",
                "resources": CRISIS_RESOURCES}
    return out


@router.delete("/journal/{entry_id}", status_code=204)
def delete_journal(entry_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.JournalEntry, entry_id, user))
    db.commit()


@router.delete("/journal", status_code=204)
def clear_journal(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(m.JournalEntry).where(m.JournalEntry.user_id == user.id))
    db.commit()


@router.get("/journal/mood")
def mood(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=60)
    rows = db.execute(select(m.JournalEntry.day, func.avg(m.JournalEntry.mood)).where(
        m.JournalEntry.user_id == user.id, m.JournalEntry.day >= since, m.JournalEntry.mood.is_not(None)).group_by(m.JournalEntry.day).order_by(m.JournalEntry.day)).all()
    return [{"day": d.isoformat(), "mood": round(float(v), 1)} for d, v in rows]


@router.get("/journal/prompts")
def prompts(_: m.User = Depends(current_user)):
    return {"prompts": PROMPTS, "boundaries": [
        "This is a place to reflect. It is not therapy and cannot diagnose anything.",
        "If you are struggling for more than a couple of weeks, or things feel unmanageable, please talk to a qualified professional.",
        "Nothing here is measured, scored or ranked."]}

"""Opt-in parent or guardian view. The student creates a link, chooses what it shows, and can cancel it at any time.

Never included: journal, mood, applications, resumes, defence answers, community activity, mentor messages,
assessment scores, or anything from the wellness area.
"""
import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import current_user
from ..models import utcnow
from ..services import badges

router = APIRouter(prefix="/v1/me/parent-links", tags=["parent-view"])
public_router = APIRouter(prefix="/v1/parent-view", tags=["parent-view"])
MAX_ACTIVE = 3


def _hash(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


class LinkIn(BaseModel):
    label: str | None = Field(default=None, max_length=60)
    show_activity: bool = True
    show_badges: bool = True
    show_topics: bool = False
    days: int = Field(default=30, ge=1, le=90)


def _out(x: m.ParentShare) -> dict:
    return {"id": x.id, "label": x.label, "show_activity": x.show_activity, "show_badges": x.show_badges, "show_topics": x.show_topics,
            "created_on": x.created_at.date().isoformat(), "expires_on": x.expires_at.date().isoformat(),
            "active": x.revoked_at is None and x.expires_at > utcnow()}


@router.get("")
def list_links(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.ParentShare).where(m.ParentShare.user_id == user.id).order_by(m.ParentShare.id.desc()).limit(20)).all()
    return {"links": [_out(r) for r in rows],
            "note": "A parent link shows only what you tick. It never shows your journal, wellness, applications, resumes, messages or scores. Cancel it any time."}


@router.post("", status_code=201)
def create_link(body: LinkIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    active = [r for r in db.scalars(select(m.ParentShare).where(m.ParentShare.user_id == user.id)) if r.revoked_at is None and r.expires_at > utcnow()]
    if len(active) >= MAX_ACTIVE:
        raise HTTPException(409, f"You can have {MAX_ACTIVE} active links. Cancel one first.")
    token = secrets.token_urlsafe(24)
    row = m.ParentShare(user_id=user.id, token_hash=_hash(token), label=body.label, show_activity=body.show_activity,
                        show_badges=body.show_badges, show_topics=body.show_topics, expires_at=utcnow() + timedelta(days=body.days))
    db.add(row)
    db.commit()
    return _out(row) | {"token": token, "path": f"/parent/{token}", "note": "Shown once. Anyone with this link can see what you ticked until it expires or you cancel it."}


@router.delete("/{link_id}", status_code=204)
def revoke(link_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(m.ParentShare, link_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "Not found")
    row.revoked_at = utcnow()
    db.commit()


@public_router.get("/{token}")
def view(token: str, db: Session = Depends(get_db)):
    row = db.scalar(select(m.ParentShare).where(m.ParentShare.token_hash == _hash(token)))
    if row is None or row.revoked_at is not None or row.expires_at <= utcnow():
        raise HTTPException(404, "This link is not available. It may have expired or been cancelled.")
    out: dict = {"label": row.label, "expires_on": row.expires_at.date().isoformat(),
                 "note": "Shared by the student, who chose what appears here. It is not a report card and is not a measure of the student's worth."}
    if row.show_activity:
        out["activity"] = badges.streak(db, row.user_id)
    if row.show_badges:
        keys = [b.badge_key for b in db.scalars(select(m.UserBadge).where(m.UserBadge.user_id == row.user_id))]
        out["badges"] = [{"title": badges.BADGES[k][0], "description": badges.BADGES[k][1]} for k in keys if k in badges.BADGES]
        out["badge_note"] = badges.INTERNAL_NOTE
    if row.show_topics:
        out["topics"] = [{"pillar": t.pillar, "topic": t.topic, "attempts": t.attempts}
                         for t in db.scalars(select(m.TopicProgress).where(m.TopicProgress.user_id == row.user_id).order_by(m.TopicProgress.pillar))]
    return out

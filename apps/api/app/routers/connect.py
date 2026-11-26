"""Community boards, mentors and moderation. Everything here needs sign-in and uses a chosen handle, never an email."""
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import meta
from .. import models as m
from ..db import get_db
from ..deps import current_user, reviewer_or_above
from ..services.safety import CRISIS_RESOURCES, contains_contact_details, crisis_signal

router = APIRouter(prefix="/v1", tags=["connect"])
admin_router = APIRouter(prefix="/v1/moderation", tags=["moderation"])
HOURLY_LIMIT = 10
REPORT_HIDE_AT = 3
HANDLE_RE = re.compile(r"^[a-z0-9_]{3,30}$")
RESERVED = {"admin", "samarthya", "moderator", "support", "staff", "official"}
GUIDELINES = [
    "Be kind and specific. Disagree with ideas, not people.",
    "Do not share phone numbers, emails, social handles or addresses. Posts that contain them are blocked.",
    "No harassment, discrimination, or pressure on anyone to share personal details.",
    "This is not a place for medical, legal or financial advice from strangers.",
    "If you are struggling, please use the helplines on the Live page.",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _member(db: Session, user: m.User) -> m.Member:
    mem = db.get(m.Member, user.id)
    if mem is None:
        raise HTTPException(403, "Choose a handle before joining the community")
    return mem


# ---------------------------------------------------------------- identity
class HandleIn(BaseModel):
    handle: str

    @field_validator("handle")
    @classmethod
    def _h(cls, v):
        v = v.strip().lower()
        if not HANDLE_RE.match(v):
            raise ValueError("3 to 30 characters: lowercase letters, numbers and underscores")
        if v in RESERVED or "samarthya" in v:
            raise ValueError("That handle is not available")
        return v


@router.get("/community/me")
def community_me(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mem = db.get(m.Member, user.id)
    return {"handle": mem.handle if mem else None, "guidelines": GUIDELINES}


@router.put("/community/me")
def set_handle(body: HandleIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    taken = db.scalar(select(m.Member).where(m.Member.handle == body.handle, m.Member.user_id != user.id))
    if taken:
        raise HTTPException(409, "That handle is taken")
    mem = db.get(m.Member, user.id) or m.Member(user_id=user.id, handle=body.handle)
    mem.handle = body.handle
    db.add(mem)
    db.commit()
    return {"handle": mem.handle}


# ---------------------------------------------------------------- boards
@router.get("/community/boards")
def boards(_: m.User = Depends(current_user), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(m.Post.board, func.count()).where(m.Post.status == "visible").group_by(m.Post.board)).all())
    return {"boards": [{"slug": k, "name": v, "posts": counts.get(k, 0)} for k, v in meta.BOARDS.items()], "guidelines": GUIDELINES}


def _post_out(p: m.Post, with_replies: bool = False) -> dict:
    d = {"id": p.id, "board": p.board, "title": p.title, "author": p.author.handle if p.author else "deleted", "created_at": p.created_at.isoformat(),
         "replies": sum(1 for r in p.replies if r.status == "visible")}
    if with_replies:
        d["body"] = p.body
        d["replies_list"] = [{"id": r.id, "body": r.body, "author": r.author.handle if r.author else "deleted", "created_at": r.created_at.isoformat()}
                             for r in sorted(p.replies, key=lambda r: r.id) if r.status == "visible"]
    return d


@router.get("/community/boards/{board}/posts")
def posts(board: str, offset: int = 0, _: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if board not in meta.BOARDS:
        raise HTTPException(404, "Not found")
    rows = db.scalars(select(m.Post).where(m.Post.board == board, m.Post.status == "visible").order_by(m.Post.id.desc())
                      .offset(max(0, offset)).limit(30)).all()
    return [_post_out(p) for p in rows]


@router.get("/community/posts/{post_id}")
def get_post(post_id: int, _: m.User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(m.Post, post_id)
    if p is None or p.status != "visible":
        raise HTTPException(404, "Not found")
    return _post_out(p, with_replies=True)


class PostIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=4000)


class ReplyIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


def _check_text(db: Session, user: m.User, *texts: str):
    for t in texts:
        if contains_contact_details(t):
            raise HTTPException(422, "Please remove phone numbers, email addresses, links to private chats and social handles. This keeps everyone safe.")
    since = _now() - timedelta(hours=1)
    n = (db.scalar(select(func.count()).select_from(m.Post).where(m.Post.author_id == user.id, m.Post.created_at >= since)) or 0) + \
        (db.scalar(select(func.count()).select_from(m.Reply).where(m.Reply.author_id == user.id, m.Reply.created_at >= since)) or 0)
    if n >= HOURLY_LIMIT:
        raise HTTPException(429, "You have posted a lot in the last hour. Please take a break and come back soon.")


def _crisis_note(text: str) -> dict:
    if crisis_signal(text):
        return {"care": "If any of this is about you, please reach out to someone now. These services are free and confidential.", "resources": CRISIS_RESOURCES}
    return {}


@router.post("/community/boards/{board}/posts", status_code=201)
def create_post(board: str, body: PostIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if board not in meta.BOARDS:
        raise HTTPException(404, "Not found")
    _member(db, user)
    _check_text(db, user, body.title, body.body)
    p = m.Post(board=board, author_id=user.id, title=body.title.strip(), body=body.body.strip())
    db.add(p)
    db.commit()
    return {"id": p.id} | _crisis_note(body.title + " " + body.body)


@router.post("/community/posts/{post_id}/replies", status_code=201)
def reply(post_id: int, body: ReplyIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(m.Post, post_id)
    if p is None or p.status != "visible":
        raise HTTPException(404, "Not found")
    _member(db, user)
    _check_text(db, user, body.body)
    r = m.Reply(post_id=p.id, author_id=user.id, body=body.body.strip())
    db.add(r)
    db.commit()
    return {"id": r.id} | _crisis_note(body.body)


@router.delete("/community/posts/{post_id}", status_code=204)
def delete_post(post_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(m.Post, post_id)
    if p is None or p.author_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(p)
    db.commit()


@router.delete("/community/replies/{reply_id}", status_code=204)
def delete_reply(reply_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(m.Reply, reply_id)
    if r is None or r.author_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(r)
    db.commit()


class ReportIn(BaseModel):
    kind: str
    target_id: int
    reason: str = Field(min_length=3, max_length=300)

    @field_validator("kind")
    @classmethod
    def _k(cls, v):
        if v not in ("post", "reply", "mentor"):
            raise ValueError("kind must be post, reply or mentor")
        return v


@router.post("/community/reports", status_code=201)
def report(body: ReportIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    target = {"post": lambda: db.get(m.Post, body.target_id), "reply": lambda: db.get(m.Reply, body.target_id),
              "mentor": lambda: db.get(m.Mentor, body.target_id)}[body.kind]()
    if target is None:
        raise HTTPException(404, "Not found")
    if db.scalar(select(m.ContentReport).where(m.ContentReport.reporter_id == user.id, m.ContentReport.kind == body.kind,
                                               m.ContentReport.target_id == body.target_id)):
        return {"ok": True, "note": "You already reported this."}
    db.add(m.ContentReport(kind=body.kind, target_id=body.target_id, reporter_id=user.id, reason=body.reason.strip()))
    db.flush()
    n = db.scalar(select(func.count()).select_from(m.ContentReport).where(
        m.ContentReport.kind == body.kind, m.ContentReport.target_id == body.target_id, m.ContentReport.handled.is_(False))) or 0
    if n >= REPORT_HIDE_AT:
        if body.kind == "mentor" and target.status == "approved":
            target.status = "paused"
        elif body.kind != "mentor" and target.status == "visible":
            target.status = "hidden"
    db.commit()
    return {"ok": True, "note": "Thank you. A moderator will look at this."}


# ---------------------------------------------------------------- moderation
@admin_router.get("/reports")
def open_reports(_: m.User = Depends(reviewer_or_above), db: Session = Depends(get_db)):
    out = []
    for r in db.scalars(select(m.ContentReport).where(m.ContentReport.handled.is_(False)).order_by(m.ContentReport.id).limit(200)):
        text = None
        if r.kind == "post" and (p := db.get(m.Post, r.target_id)):
            text, status = f"{p.title}: {p.body}", p.status
        elif r.kind == "reply" and (x := db.get(m.Reply, r.target_id)):
            text, status = x.body, x.status
        elif r.kind == "mentor" and (mm := db.get(m.Mentor, r.target_id)):
            text, status = f"{mm.display_name}: {mm.headline}", mm.status
        else:
            status = "gone"
        out.append({"id": r.id, "kind": r.kind, "target_id": r.target_id, "reason": r.reason, "content": text, "status": status,
                    "created_at": r.created_at.isoformat()})
    return out


class ModerateIn(BaseModel):
    action: str  # restore, remove, dismiss

    @field_validator("action")
    @classmethod
    def _a(cls, v):
        if v not in ("restore", "remove", "dismiss"):
            raise ValueError("action must be restore, remove or dismiss")
        return v


@admin_router.post("/reports/{report_id}")
def moderate(report_id: int, body: ModerateIn, _: m.User = Depends(reviewer_or_above), db: Session = Depends(get_db)):
    r = db.get(m.ContentReport, report_id)
    if r is None:
        raise HTTPException(404, "Not found")
    model = {"post": m.Post, "reply": m.Reply, "mentor": m.Mentor}[r.kind]
    target = db.get(model, r.target_id)
    if target is not None and body.action != "dismiss":
        if r.kind == "mentor":
            target.status = "approved" if body.action == "restore" else "rejected"
        else:
            target.status = "visible" if body.action == "restore" else "removed"
    for other in db.scalars(select(m.ContentReport).where(m.ContentReport.kind == r.kind, m.ContentReport.target_id == r.target_id)):
        other.handled = True
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- mentors
class MentorIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    headline: str = Field(min_length=3, max_length=200)
    bio: str = Field(min_length=20, max_length=2000)
    kind: str
    expertise: list[str] = Field(default_factory=list, max_length=10)
    languages: list[str] = Field(default_factory=list, max_length=10)
    profile_url: str = Field(max_length=2048)

    @field_validator("kind")
    @classmethod
    def _k(cls, v):
        if v not in meta.MENTOR_KINDS:
            raise ValueError("kind must be one of: " + ", ".join(sorted(meta.MENTOR_KINDS)))
        return v

    @field_validator("profile_url")
    @classmethod
    def _u(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Give a public profile link (https://) so a reviewer can check who you are")
        return v

    @field_validator("bio", "headline")
    @classmethod
    def _c(cls, v):
        if contains_contact_details(v):
            raise ValueError("Please do not put contact details in your profile")
        return v


def _mentor_out(mm: m.Mentor, private: bool = False) -> dict:
    d = {"id": mm.user_id, "display_name": mm.display_name, "headline": mm.headline, "bio": mm.bio, "kind": mm.kind,
         "expertise": mm.expertise, "languages": mm.languages, "profile_url": mm.profile_url}
    if private:
        d["status"] = mm.status
    return d


@router.get("/mentors")
def mentors(kind: str | None = None, q: str | None = None, _: m.User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(m.Mentor).where(m.Mentor.status == "approved").order_by(m.Mentor.created_at.desc()).limit(200)
    rows = db.scalars(stmt).all()
    if kind:
        rows = [r for r in rows if r.kind == kind]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in (r.display_name + " " + r.headline + " " + " ".join(r.expertise or [])).lower()]
    return {"mentors": [_mentor_out(r) for r in rows],
            "note": "Mentors are volunteers and are checked against a public profile before approval. Samarthya cannot guarantee any individual's advice."}


@router.get("/mentors/me")
def my_mentor(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, user.id)
    return _mentor_out(mm, private=True) if mm else None


@router.put("/mentors/me")
def apply_mentor(body: MentorIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, user.id)
    if mm is None:
        mm = m.Mentor(user_id=user.id, status="pending")
    elif mm.status in ("rejected",):
        raise HTTPException(403, "This application was not approved. Please contact the team.")
    else:
        mm.status = "pending"  # any edit goes back for review
    for k, v in body.model_dump().items():
        setattr(mm, k, v)
    db.add(mm)
    db.commit()
    return _mentor_out(mm, private=True)


@router.delete("/mentors/me", status_code=204)
def leave_mentors(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, user.id)
    if mm:
        db.delete(mm)
        db.commit()


class MentorRequestIn(BaseModel):
    message: str = Field(min_length=20, max_length=1500)
    share_contact: str | None = Field(default=None, max_length=320)


@router.post("/mentors/{mentor_id}/requests", status_code=201)
def request_mentor(mentor_id: int, body: MentorRequestIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, mentor_id)
    if mm is None or mm.status != "approved":
        raise HTTPException(404, "Not found")
    if mm.user_id == user.id:
        raise HTTPException(422, "You cannot request yourself")
    if contains_contact_details(body.message):
        raise HTTPException(422, "Please keep contact details out of the message. You can choose to share one separately.")
    pending = db.scalar(select(func.count()).select_from(m.MentorRequest).where(m.MentorRequest.student_id == user.id, m.MentorRequest.status == "pending")) or 0
    if pending >= 3:
        raise HTTPException(429, "You have 3 requests waiting. Please wait for replies first.")
    if db.scalar(select(m.MentorRequest).where(m.MentorRequest.student_id == user.id, m.MentorRequest.mentor_id == mentor_id,
                                               m.MentorRequest.status == "pending")):
        raise HTTPException(409, "You already have a request waiting with this mentor")
    req = m.MentorRequest(student_id=user.id, mentor_id=mentor_id, message=body.message.strip(), share_contact=(body.share_contact or "").strip() or None)
    db.add(req)
    db.commit()
    return {"id": req.id, "note": "Your message has been sent. Your email is not shared unless you included it."}


def _handle(db: Session, uid: int) -> str:
    mem = db.get(m.Member, uid)
    return mem.handle if mem else "a student"


@router.get("/mentors/requests/received")
def received(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, user.id)
    if mm is None:
        raise HTTPException(403, "You are not a mentor")
    rows = db.scalars(select(m.MentorRequest).where(m.MentorRequest.mentor_id == user.id).order_by(m.MentorRequest.id.desc()).limit(100))
    return [{"id": r.id, "from": _handle(db, r.student_id), "message": r.message, "status": r.status,
             "contact": r.share_contact if r.status == "accepted" else None, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/mentors/requests/sent")
def sent(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.MentorRequest).where(m.MentorRequest.student_id == user.id).order_by(m.MentorRequest.id.desc()).limit(100))
    out = []
    for r in rows:
        mm = db.get(m.Mentor, r.mentor_id)
        out.append({"id": r.id, "mentor": mm.display_name if mm else "(no longer a mentor)", "message": r.message, "status": r.status,
                    "reply": r.reply, "created_at": r.created_at.isoformat()})
    return out


class RespondIn(BaseModel):
    action: str
    reply: str | None = Field(default=None, max_length=1500)

    @field_validator("action")
    @classmethod
    def _a(cls, v):
        if v not in ("accept", "decline", "close"):
            raise ValueError("action must be accept, decline or close")
        return v


@router.post("/mentors/requests/{request_id}/respond")
def respond(request_id: int, body: RespondIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(m.MentorRequest, request_id)
    if r is None or r.mentor_id != user.id:
        raise HTTPException(404, "Not found")
    if body.reply and contains_contact_details(body.reply):
        raise HTTPException(422, "Please keep contact details out of the reply. Accepted requests share only what the student chose to include.")
    r.status = {"accept": "accepted", "decline": "declined", "close": "closed"}[body.action]
    r.reply = body.reply
    db.commit()
    return {"status": r.status}


@admin_router.get("/mentors/pending")
def pending_mentors(_: m.User = Depends(reviewer_or_above), db: Session = Depends(get_db)):
    return [_mentor_out(r, private=True) for r in db.scalars(select(m.Mentor).where(m.Mentor.status == "pending").order_by(m.Mentor.created_at))]


class MentorDecision(BaseModel):
    decision: str

    @field_validator("decision")
    @classmethod
    def _d(cls, v):
        if v not in ("approve", "reject", "pause"):
            raise ValueError("decision must be approve, reject or pause")
        return v


@admin_router.post("/mentors/{mentor_id}")
def decide_mentor(mentor_id: int, body: MentorDecision, reviewer: m.User = Depends(reviewer_or_above), db: Session = Depends(get_db)):
    mm = db.get(m.Mentor, mentor_id)
    if mm is None:
        raise HTTPException(404, "Not found")
    if mm.user_id == reviewer.id:
        raise HTTPException(403, "You cannot approve your own mentor profile")
    mm.status = {"approve": "approved", "reject": "rejected", "pause": "paused"}[body.decision]
    db.commit()
    return {"status": mm.status}

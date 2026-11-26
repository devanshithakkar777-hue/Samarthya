"""Study notes, concept maps, study assistant, mock interviewer, group mentoring sessions, employer / professional /
entrepreneur dashboards, company prep packs, career-switch roadmaps and partner credentials.

Privacy: everything a student writes here is private to them. Counts shown to employers and mentors are numbers
only, and only for groups of at least K_MIN. Nothing here exposes names, journals or wellness data.
"""
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import admin_only, current_user
from ..models import utcnow
from ..services import ask, llm
from ..services.provenance import provenance
from ..services.safety import CRISIS_RESOURCES, crisis_signal
from .me_learn import _ai_allowed

router = APIRouter(prefix="/v1", tags=["study-business"])
K_MIN = 10
PUB = m.Status.published


def _own(db: Session, model, obj_id: int, user: m.User):
    row = db.get(model, obj_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Not found")
    return row


def _item(db: Session, slug: str) -> m.LibraryItem:
    it = db.scalar(select(m.LibraryItem).where(m.LibraryItem.slug == slug, m.LibraryItem.status == PUB))
    if not it:
        raise HTTPException(404, "Library item not found")
    return it


# ------------------------------------------------------------------ highlights and notes on library items
class NoteIn(BaseModel):
    kind: str = Field(default="note", pattern="^(note|highlight)$")
    quote: str | None = Field(default=None, max_length=300)
    body: str = Field(default="", max_length=2000)


def _note(n: m.LibraryNote) -> dict:
    return {"id": n.id, "kind": n.kind, "quote": n.quote, "body": n.body, "created_on": n.created_at.date().isoformat()}


@router.get("/me/library-notes/{slug}")
def list_notes(slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    it = _item(db, slug)
    rows = db.scalars(select(m.LibraryNote).where(m.LibraryNote.user_id == user.id, m.LibraryNote.item_id == it.id).order_by(m.LibraryNote.id)).all()
    return {"item": {"slug": it.slug, "title": it.title, "access_url": it.access_url},
            "notes": [_note(n) for n in rows],
            "hint": "Open the book from its own site, then type the short passage you want to remember here, in your own words or as a short quote. Samarthya does not store the book."}


@router.post("/me/library-notes/{slug}", status_code=201)
def add_note(slug: str, body: NoteIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if not (body.quote or body.body.strip()):
        raise HTTPException(422, "Write a note or a short quote")
    it = _item(db, slug)
    if db.scalar(select(func.count()).select_from(m.LibraryNote).where(m.LibraryNote.user_id == user.id)) >= 500:
        raise HTTPException(409, "You have reached 500 notes. Delete some first.")
    n = m.LibraryNote(user_id=user.id, item_id=it.id, kind=body.kind, quote=body.quote, body=body.body.strip())
    db.add(n)
    db.commit()
    return _note(n)


@router.delete("/me/library-notes/note/{note_id}", status_code=204)
def delete_note(note_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.LibraryNote, note_id, user))
    db.commit()


# ------------------------------------------------------------------ concept maps
class MapIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    nodes: list[dict] = Field(default_factory=list, max_length=60)
    edges: list[dict] = Field(default_factory=list, max_length=120)

    @field_validator("nodes")
    @classmethod
    def _nodes(cls, v):
        out = []
        for n in v:
            if not isinstance(n.get("id"), (str, int)) or not str(n.get("label", "")).strip():
                raise ValueError("Each node needs an id and a label")
            out.append({"id": str(n["id"])[:20], "label": str(n["label"])[:80], "x": float(n.get("x", 0) or 0), "y": float(n.get("y", 0) or 0)})
        if len({n["id"] for n in out}) != len(out):
            raise ValueError("Node ids must be unique")
        return out


def _clean_edges(body: MapIn) -> list[dict]:
    ids = {n["id"] for n in body.nodes}
    out = []
    for e in body.edges:
        a, b = str(e.get("from", "")), str(e.get("to", ""))
        if a not in ids or b not in ids:
            raise HTTPException(422, "Every link must join two existing boxes")
        out.append({"from": a, "to": b, "label": str(e.get("label", ""))[:60]})
    return out


def _map(x: m.ConceptMap, full: bool = True) -> dict:
    d = {"id": x.id, "title": x.title, "updated_on": x.updated_at.date().isoformat(), "boxes": len((x.data or {}).get("nodes", []))}
    if full:
        d |= {"nodes": (x.data or {}).get("nodes", []), "edges": (x.data or {}).get("edges", [])}
    return d


@router.get("/me/concept-maps")
def list_maps(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return {"maps": [_map(x, False) for x in db.scalars(select(m.ConceptMap).where(m.ConceptMap.user_id == user.id).order_by(m.ConceptMap.updated_at.desc()).limit(100))]}


@router.post("/me/concept-maps", status_code=201)
def create_map(body: MapIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    x = m.ConceptMap(user_id=user.id, title=body.title, data={"nodes": body.nodes, "edges": _clean_edges(body)})
    db.add(x)
    db.commit()
    return _map(x)


@router.get("/me/concept-maps/{map_id}")
def get_map(map_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return _map(_own(db, m.ConceptMap, map_id, user))


@router.put("/me/concept-maps/{map_id}")
def update_map(map_id: int, body: MapIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    x = _own(db, m.ConceptMap, map_id, user)
    x.title, x.data = body.title, {"nodes": body.nodes, "edges": _clean_edges(body)}
    db.commit()
    return _map(x)


@router.delete("/me/concept-maps/{map_id}", status_code=204)
def delete_map(map_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.ConceptMap, map_id, user))
    db.commit()


# ------------------------------------------------------------------ study assistant (over sourced pages and the student's own notes)
class StudyIn(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    library_slug: str | None = None


@router.post("/me/study-assistant")
def study_assistant(body: StudyIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Answers from Samarthya's sourced pages plus the student's own notes on one library item.
    It cannot read the books themselves: they are links to other sites."""
    q = " ".join(body.question.split())
    if crisis_signal(q):
        return {"mode": "safety", "answer": "I'm sorry you're feeling this way. Please talk to someone now; these free services are open. If you are in danger call 112.",
                "citations": [], "crisis_resources": CRISIS_RESOURCES, "own_notes": []}
    passages = ask.top_passages(db, q)
    own = []
    if body.library_slug:
        it = _item(db, body.library_slug)
        rows = db.scalars(select(m.LibraryNote).where(m.LibraryNote.user_id == user.id, m.LibraryNote.item_id == it.id)).all()
        qt = set(ask.tokens(q))
        for n in rows:
            text = " ".join(x for x in (n.quote, n.body) if x)
            if qt & set(ask.tokens(text)):
                own.append({"title": f"Your note on {it.title}", "text": text})
        passages = ([{"title": o["title"], "text": o["text"], "path": f"/library/{it.slug}", "kind": "your-note"} for o in own[:4]] + list(passages))[:8]
    note_base = "The study assistant uses Samarthya's sourced pages and your own notes. It cannot read books, so check the book itself for exact wording."
    if llm.enabled():
        if not _ai_allowed(user.id):
            raise HTTPException(429, "You have reached today's limit for the AI features.")
        try:
            res = llm.chat(q, passages)
            return {"mode": "ai", **res, "own_notes": own[:4], "note": "AI-written. " + note_base}
        except llm.LlmUnavailable:
            pass
    res = ask.answer(db, q)
    return {"mode": "retrieval", "answer": res["answer"], "citations": res["citations"], "own_notes": own[:4],
            "note": "The AI assistant is not switched on, so this is copied from sourced pages. " + note_base}


# ------------------------------------------------------------------ mock interviewer
STARTERS = [  # generic practice prompts: not facts, no source needed
    ("Tell me about yourself.", "Short and relevant: who you are now, what you have done, what you want next."),
    ("Describe a time you worked in a team and something went wrong.", "Situation, your own part, what you did, the result, what you learned."),
    ("Why do you want this role?", "Specific reasons tied to the role's work and your experience, not general praise."),
    ("Tell me about a project you are proud of.", "What it was, your own contribution, a number or concrete result, what you would change."),
    ("How do you handle a deadline you might miss?", "Early warning, priorities, asking for help, a real example."),
    ("What is a weakness you are working on?", "A real one, with what you are doing about it, without disguising a strength."),
]
STAR = {"situation": r"\b(when|during|at|in my)\b", "task": r"\b(my (task|role|goal)|i (was|had) to|needed to)\b",
        "action": r"\b(i (built|wrote|led|organised|organized|decided|created|fixed|asked|planned|tested|learned|learnt))\b",
        "result": r"\b(result|resulted|led to|improved|reduced|increased|saved|finished|delivered|learned|learnt|\d+)\b"}


class StartIn(BaseModel):
    role_slug: str | None = None
    count: int = Field(default=4, ge=1, le=8)


def _turn_question(db: Session, slug: str):
    if slug.startswith("starter-"):
        i = int(slug.split("-")[1])
        return STARTERS[i][0], STARTERS[i][1]
    q = db.scalar(select(m.Question).where(m.Question.slug == slug))
    return (q.stem, q.guidance or "") if q else ("", "")


@router.post("/me/mock-interview", status_code=201)
def mock_start(body: StartIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    role = None
    if body.role_slug:
        role = db.scalar(select(m.Role).where(m.Role.slug == body.role_slug, m.Role.status == PUB))
        if not role:
            raise HTTPException(404, "Role not found")
    qs = select(m.Question).where(m.Question.status == PUB, m.Question.kind == "open")
    if role:
        qs = qs.where((m.Question.role_id == role.id) | (m.Question.role_id.is_(None)))
    pool = [q.slug for q in db.scalars(qs.order_by(func.random()).limit(body.count))]
    slugs = pool + [f"starter-{i}" for i in range(len(STARTERS))]
    slugs = slugs[: body.count]
    row = m.MockInterview(user_id=user.id, role_slug=role.slug if role else None, question_slugs=slugs, turns=[])
    db.add(row)
    db.commit()
    return _mock(db, row)


def _mock(db: Session, x: m.MockInterview) -> dict:
    i = len(x.turns)
    q = None
    if i < len(x.question_slugs):
        q = {"n": i + 1, "of": len(x.question_slugs), "text": _turn_question(db, x.question_slugs[i])[0]}
    return {"id": x.id, "finished": x.finished or q is None, "next_question": q, "turns": x.turns, "ai": llm.enabled(),
            "note": "Practice only. Feedback checks structure and coverage; it cannot tell whether your experiences are true and it does not predict results."}


def rule_feedback(answer: str, guidance: str) -> dict:
    words = answer.split()
    low = answer.lower()
    strengths, improvements = [], []
    if 40 <= len(words) <= 220:
        strengths.append("A useful length: long enough to be specific, short enough to hold attention.")
    elif len(words) < 40:
        improvements.append("Too short to show much. Add what you actually did and what happened.")
    else:
        improvements.append("Quite long. Aim for about 1 to 2 minutes spoken; cut the background.")
    hit = [k for k, rx in STAR.items() if re.search(rx, low)]
    missing = [k for k in STAR if k not in hit]
    if len(hit) >= 3:
        strengths.append("Your answer covers most of situation, task, action and result.")
    if missing:
        improvements.append("Check these parts: " + ", ".join(missing) + ".")
    if re.search(r"\bwe\b", low) and not re.search(r"\bi\b", low):
        improvements.append("You say 'we' throughout. Say clearly what you did yourself.")
    if re.search(r"\d", answer):
        strengths.append("You gave a number or concrete detail.")
    else:
        improvements.append("Add one concrete detail, such as a number, a name of a tool, or a date.")
    covered = None
    if guidance:
        g, a = set(ask.tokens(guidance)), set(ask.tokens(answer))
        covered = round(len(g & a) / max(1, len(g)), 2)
        if covered >= 0.25:
            strengths.append("You touched the points this question usually looks for.")
        else:
            improvements.append("Re-read what this question usually looks for: " + guidance[:160])
    return {"strengths": strengths[:4], "improvements": improvements[:4], "scores": {}, "mode": "rules"}


class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


@router.post("/me/mock-interview/{iid}/answer")
def mock_answer(iid: int, body: AnswerIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    x = _own(db, m.MockInterview, iid, user)
    if x.finished or len(x.turns) >= len(x.question_slugs):
        raise HTTPException(409, "This practice interview is finished")
    if crisis_signal(body.answer):
        return {"mode": "safety", "answer": "If any of this is about you, please talk to someone now. These services are free.", "crisis_resources": CRISIS_RESOURCES}
    text, guidance = _turn_question(db, x.question_slugs[len(x.turns)])
    fb = None
    if llm.enabled() and _ai_allowed(user.id):
        try:
            fb = llm.evaluate(text, guidance, body.answer) | {"mode": "ai"}
        except llm.LlmUnavailable:
            fb = None
    fb = fb or rule_feedback(body.answer, guidance)
    x.turns = [*x.turns, {"question": text, "answer": body.answer[:4000], "feedback": fb}]
    x.finished = len(x.turns) >= len(x.question_slugs)
    db.commit()
    return _mock(db, x)


@router.get("/me/mock-interview")
def mock_list(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.MockInterview).where(m.MockInterview.user_id == user.id).order_by(m.MockInterview.id.desc()).limit(20)).all()
    return {"interviews": [{"id": r.id, "role_slug": r.role_slug, "answered": len(r.turns), "of": len(r.question_slugs), "finished": r.finished,
                            "date": r.created_at.date().isoformat()} for r in rows]}


@router.get("/me/mock-interview/{iid}")
def mock_get(iid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return _mock(db, _own(db, m.MockInterview, iid, user))


@router.delete("/me/mock-interview/{iid}", status_code=204)
def mock_delete(iid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.MockInterview, iid, user))
    db.commit()


# ------------------------------------------------------------------ group mentoring sessions
def _approved_mentor(db: Session, user: m.User) -> m.Mentor:
    me = db.get(m.Mentor, user.id)
    if not me or me.status != "approved":
        raise HTTPException(403, "Only approved mentors can do this")
    return me


class SessionIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=2000)
    starts_at: datetime
    minutes: int = Field(default=45, ge=15, le=180)
    capacity: int = Field(default=10, ge=2, le=50)
    meeting_details: str | None = Field(default=None, max_length=500)


def _seats(db: Session, sid: int) -> int:
    return db.scalar(select(func.count()).select_from(m.MentorSessionSeat).where(m.MentorSessionSeat.session_id == sid)) or 0


def _session(db: Session, s: m.MentorSession, mentor: m.Mentor | None, uid: int | None = None, joined: bool = False) -> dict:
    d = {"id": s.id, "title": s.title, "description": s.description, "starts_at": s.starts_at.isoformat(), "minutes": s.minutes,
         "capacity": s.capacity, "seats_taken": _seats(db, s.id), "mentor": mentor.display_name if mentor else None,
         "mentor_headline": mentor.headline if mentor else None, "joined": joined}
    if joined:
        d["meeting_details"] = s.meeting_details
    return d


@router.get("/mentor-sessions")
def upcoming_sessions(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.MentorSession).join(m.Mentor, m.Mentor.user_id == m.MentorSession.mentor_id)
                      .where(m.MentorSession.cancelled.is_(False), m.MentorSession.starts_at > utcnow(), m.Mentor.status == "approved")
                      .order_by(m.MentorSession.starts_at).limit(50)).all()
    mine = {s.session_id for s in db.scalars(select(m.MentorSessionSeat).where(m.MentorSessionSeat.user_id == user.id))}
    return {"sessions": [_session(db, s, db.get(m.Mentor, s.mentor_id), joined=s.id in mine) for s in rows],
            "note": "Group sessions are run by approved mentors on their own meeting tools. Samarthya does not host calls or record them. Never share personal contact details in a group."}


@router.post("/mentors/me/sessions", status_code=201)
def create_session(body: SessionIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    me = _approved_mentor(db, user)
    when = body.starts_at if body.starts_at.tzinfo else body.starts_at.replace(tzinfo=timezone.utc)
    if when <= utcnow():
        raise HTTPException(422, "Choose a time in the future")
    s = m.MentorSession(mentor_id=user.id, title=body.title, description=body.description, starts_at=when, minutes=body.minutes,
                        capacity=body.capacity, meeting_details=body.meeting_details)
    db.add(s)
    db.commit()
    return _session(db, s, me, joined=True)


@router.post("/mentors/me/sessions/{sid}/cancel")
def cancel_session(sid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _approved_mentor(db, user)
    s = db.get(m.MentorSession, sid)
    if not s or s.mentor_id != user.id:
        raise HTTPException(404, "Not found")
    s.cancelled = True
    db.commit()
    return {"ok": True}


@router.post("/mentor-sessions/{sid}/join", status_code=201)
def join_session(sid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.get(m.MentorSession, sid)
    mentor = db.get(m.Mentor, s.mentor_id) if s else None
    if not s or s.cancelled or s.starts_at <= utcnow() or not mentor or mentor.status != "approved":
        raise HTTPException(404, "This session is not open")
    if s.mentor_id == user.id:
        raise HTTPException(409, "You are the mentor for this session")
    if db.scalar(select(m.MentorSessionSeat).where(m.MentorSessionSeat.session_id == sid, m.MentorSessionSeat.user_id == user.id)):
        return _session(db, s, mentor, joined=True)
    if _seats(db, sid) >= s.capacity:
        raise HTTPException(409, "This session is full")
    db.add(m.MentorSessionSeat(session_id=sid, user_id=user.id))
    db.commit()
    return _session(db, s, mentor, joined=True)


@router.delete("/mentor-sessions/{sid}/join", status_code=204)
def leave_session(sid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    seat = db.scalar(select(m.MentorSessionSeat).where(m.MentorSessionSeat.session_id == sid, m.MentorSessionSeat.user_id == user.id))
    if seat:
        db.delete(seat)
        db.commit()


# ------------------------------------------------------------------ professional (mentor) dashboard
@router.get("/professional/dashboard")
def professional_dashboard(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    me = db.get(m.Mentor, user.id)
    if not me:
        raise HTTPException(403, "This dashboard is for mentors")
    reqs = dict(db.execute(select(m.MentorRequest.status, func.count()).where(m.MentorRequest.mentor_id == user.id).group_by(m.MentorRequest.status)).all())
    sessions = db.scalars(select(m.MentorSession).where(m.MentorSession.mentor_id == user.id, m.MentorSession.cancelled.is_(False)).order_by(m.MentorSession.starts_at.desc()).limit(30)).all()
    return {"status": me.status, "requests": {k: reqs.get(k, 0) for k in ("pending", "accepted", "declined", "closed")},
            "sessions": [{"id": s.id, "title": s.title, "starts_at": s.starts_at.isoformat(), "capacity": s.capacity, "seats_taken": _seats(db, s.id),
                          "upcoming": s.starts_at > utcnow()} for s in sessions],
            "note": "You see counts only. Student names are shown only on requests a student chose to send to you."}


# ------------------------------------------------------------------ employer dashboard
class EmployerIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,60}$")
    name: str = Field(min_length=2, max_length=200)
    website: str | None = Field(default=None, max_length=2048)
    staff_email: str = Field(min_length=5, max_length=320)


@router.post("/org-admin/employers", status_code=201)
def create_employer(body: EmployerIn, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    if db.scalar(select(m.Employer).where(m.Employer.slug == body.slug)):
        raise HTTPException(409, "That slug is taken")
    u = db.scalar(select(m.User).where(m.User.email == body.staff_email.lower().strip()))
    if not u:
        raise HTTPException(404, "That person must sign in once first")
    e = m.Employer(slug=body.slug, name=body.name, website=body.website)
    db.add(e)
    db.flush()
    db.add(m.EmployerStaff(employer_id=e.id, user_id=u.id))
    db.commit()
    return {"id": e.id, "slug": e.slug}


def _employer(db: Session, user: m.User) -> m.Employer:
    e = db.scalar(select(m.Employer).join(m.EmployerStaff, m.EmployerStaff.employer_id == m.Employer.id).where(m.EmployerStaff.user_id == user.id))
    if not e:
        raise HTTPException(403, "This dashboard is for approved employer accounts")
    return e


class EmpOppIn(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    kind: str
    description: str = Field(min_length=20, max_length=4000)
    eligibility: str = Field(min_length=5, max_length=2000)
    apply_url: str = Field(pattern=r"^https://", max_length=2048)
    location: str | None = Field(default=None, max_length=160)
    mode: str | None = None
    stipend: str | None = Field(default=None, max_length=160)
    duration_text: str | None = Field(default=None, max_length=120)


@router.post("/employer/opportunities", status_code=201)
def employer_post(body: EmpOppIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Creates a DRAFT. A Samarthya reviewer must add a source, check it, and approve it before any student sees it."""
    from .. import meta
    e = _employer(db, user)
    if body.kind not in meta.OPPORTUNITY_KINDS or (body.mode and body.mode not in meta.OPPORTUNITY_MODES):
        raise HTTPException(422, "Unknown kind or mode")
    base = re.sub(r"[^a-z0-9]+", "-", f"{e.slug}-{body.title}".lower()).strip("-")[:90]
    slug = f"{base}-{secrets.token_hex(2)}"
    o = m.Opportunity(slug=slug, title=body.title, organisation=e.name, kind=body.kind, description=body.description, eligibility=body.eligibility,
                      apply_url=body.apply_url, location=body.location, mode=body.mode, stipend=body.stipend, duration_text=body.duration_text,
                      created_by_id=user.id, status=m.Status.draft)
    db.add(o)
    db.commit()
    return {"slug": o.slug, "status": "draft", "note": "Submitted as a draft. It appears to students only after a Samarthya reviewer checks and approves it."}


@router.get("/employer/dashboard")
def employer_dashboard(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    e = _employer(db, user)
    staff = [r.user_id for r in db.scalars(select(m.EmployerStaff).where(m.EmployerStaff.employer_id == e.id))]
    opps = db.scalars(select(m.Opportunity).where(m.Opportunity.created_by_id.in_(staff)).order_by(m.Opportunity.id.desc()).limit(100)).all()
    out = []
    for o in opps:
        saves = db.scalar(select(func.count()).select_from(m.SavedItem).where(m.SavedItem.entity_type == "opportunity", m.SavedItem.entity_id == o.id)) or 0
        out.append({"slug": o.slug, "title": o.title, "status": o.status.value, "saves": saves if saves >= K_MIN else None})
    return {"employer": e.name, "opportunities": out,
            "note": f"Save counts appear only once at least {K_MIN} students have saved a listing. You never see student names or profiles."}


# ------------------------------------------------------------------ entrepreneur dashboard (student's own venture tracker)
class VentureIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    stage: str = Field(default="idea", pattern="^(idea|validating|building|launched)$")
    problem: str | None = Field(default=None, max_length=2000)
    customer: str | None = Field(default=None, max_length=2000)
    milestones: list[dict] = Field(default_factory=list, max_length=30)

    @field_validator("milestones")
    @classmethod
    def _ms(cls, v):
        return [{"text": str(x.get("text", ""))[:200], "done": bool(x.get("done"))} for x in v if str(x.get("text", "")).strip()]


def _venture(v: m.Venture) -> dict:
    done = sum(1 for x in v.milestones if x.get("done"))
    return {"id": v.id, "name": v.name, "stage": v.stage, "problem": v.problem, "customer": v.customer, "milestones": v.milestones,
            "progress": {"done": done, "total": len(v.milestones)}, "updated_on": v.updated_at.date().isoformat()}


@router.get("/me/ventures")
def list_ventures(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Venture).where(m.Venture.user_id == user.id).order_by(m.Venture.id.desc())).all()
    return {"ventures": [_venture(v) for v in rows],
            "stages": {"idea": "Write the problem and who has it", "validating": "Talk to ten real people before you build",
                       "building": "Make the smallest version that solves the problem", "launched": "Track what you learn from real customers"},
            "note": "Private to you. Samarthya gives no legal, tax or investment advice; see the Life area for the basics and speak to a professional."}


@router.post("/me/ventures", status_code=201)
def create_venture(body: VentureIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(func.count()).select_from(m.Venture).where(m.Venture.user_id == user.id)) >= 10:
        raise HTTPException(409, "You can track up to 10 ventures")
    v = m.Venture(user_id=user.id, **body.model_dump())
    db.add(v)
    db.commit()
    return _venture(v)


@router.put("/me/ventures/{vid}")
def update_venture(vid: int, body: VentureIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    v = _own(db, m.Venture, vid, user)
    for k, val in body.model_dump().items():
        setattr(v, k, val)
    db.commit()
    return _venture(v)


@router.delete("/me/ventures/{vid}", status_code=204)
def delete_venture(vid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.Venture, vid, user))
    db.commit()


# ------------------------------------------------------------------ company prep packs
@router.get("/companies/{slug}/prep")
def prep_pack(slug: str, db: Session = Depends(get_db)):
    """Everything published for preparing for one company: roles it hires for, plus lessons and open questions
    that editors tagged with the track 'prep-<company-slug>'. Empty until editors write them; nothing is invented."""
    c = db.scalar(select(m.Company).where(m.Company.slug == slug, m.Company.status == PUB))
    if not c:
        raise HTTPException(404, "Company not found")
    tag = f"prep-{c.slug}"
    lessons = db.scalars(select(m.Lesson).where(m.Lesson.track == tag, m.Lesson.status == PUB).order_by(m.Lesson.position)).all()
    qs = db.scalars(select(m.Question).where(m.Question.topic == tag, m.Question.status == PUB)).all()
    roles = [{"slug": h.role.slug, "title": h.role.title, "careers_url": h.careers_url, "last_verified": h.last_verified.isoformat()}
             for h in c.hiring if h.role.status == PUB]
    return {"company": {"slug": c.slug, "name": c.name}, "roles": roles,
            "lessons": [{"slug": x.slug, "title": x.title, "summary": x.summary, "minutes": x.minutes} for x in lessons],
            "questions": [{"slug": x.slug, "stem": x.stem, "kind": x.kind} for x in qs],
            "empty": not (lessons or qs),
            "note": "Prep packs are written and reviewed by people from official sources such as the company's own careers pages. Samarthya does not collect leaked or unofficial interview questions."}


# ------------------------------------------------------------------ career-switch roadmap
@router.get("/tools/career-switch")
def career_switch(frm: str = Query(alias="from", max_length=100), to: str = Query(max_length=100), db: Session = Depends(get_db)):
    """What a person moving from one published role to another may need to add, from the two roles' sourced requirements."""
    a, b = (db.scalar(select(m.Role).where(m.Role.slug == s, m.Role.status == PUB)) for s in (frm, to))
    if not a or not b:
        raise HTTPException(404, "Role not found")
    have = {(r.skill_id, r.label.lower().strip()) for r in a.requirements}
    have_skills = {s for s, _ in have if s}
    have_labels = {lbl for _, lbl in have}
    order = ["mandatory", "common_preference", "recommended", "differentiator"]
    gaps = []
    for r in sorted(b.requirements, key=lambda x: (order.index(x.tier.value), x.position)):
        if (r.skill_id and r.skill_id in have_skills) or r.label.lower().strip() in have_labels:
            continue
        res = []
        if r.skill_id:
            res = [{"title": x.title, "url": x.url} for x in db.scalars(select(m.LearningResource).where(m.LearningResource.skill_id == r.skill_id, m.LearningResource.status == PUB).limit(3))]
        gaps.append({"type": r.type.value, "tier": r.tier.value, "label": r.label, "note": r.note, "free_resources": res})
    shared = [r.label for r in b.requirements if (r.skill_id and r.skill_id in have_skills) or r.label.lower().strip() in have_labels]
    return {"from": {"slug": a.slug, "title": a.title}, "to": {"slug": b.slug, "title": b.title}, "already_shared": shared, "to_add": gaps,
            "sources": [provenance(a), provenance(b)],
            "note": "This compares the two roles' listed requirements. It does not predict whether you will be hired, and employers decide for themselves."}


# ------------------------------------------------------------------ partner-issued credentials
class CredIn(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    issuer: str = Field(min_length=2, max_length=200)
    title: str = Field(min_length=3, max_length=240)
    evidence_url: str = Field(pattern=r"^https://", max_length=2048)


def _cred(c: m.PartnerCredential) -> dict:
    return {"code": c.code, "issuer": c.issuer, "title": c.title, "evidence_url": c.evidence_url, "issued_on": c.issued_at.date().isoformat(),
            "revoked": c.revoked_at is not None, "kind": "partner",
            "note": f"Issued by {c.issuer}, not by Samarthya. Samarthya has recorded it and links to the partner's own evidence. It is not an accredited qualification."}


@router.post("/org-admin/credentials", status_code=201)
def record_credential(body: CredIn, admin: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    u = db.scalar(select(m.User).where(m.User.email == body.email.lower().strip()))
    if not u:
        raise HTTPException(404, "No account with that email")
    c = m.PartnerCredential(user_id=u.id, code=secrets.token_hex(6).upper(), issuer=body.issuer, title=body.title, evidence_url=body.evidence_url, recorded_by_id=admin.id)
    db.add(c)
    db.commit()
    return _cred(c)


@router.post("/org-admin/credentials/{code}/revoke")
def revoke_credential(code: str, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    c = db.scalar(select(m.PartnerCredential).where(m.PartnerCredential.code == code.upper()))
    if not c:
        raise HTTPException(404, "Not found")
    c.revoked_at = utcnow()
    db.commit()
    return _cred(c)


@router.get("/me/credentials")
def my_credentials(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.PartnerCredential).where(m.PartnerCredential.user_id == user.id).order_by(m.PartnerCredential.id.desc())).all()
    return {"credentials": [_cred(c) for c in rows]}


@router.get("/credentials/verify/{code}")
def verify_credential(code: str, db: Session = Depends(get_db)):
    """Public check of a code. Shows issuer, title and status only: never the holder's name or email."""
    c = db.scalar(select(m.PartnerCredential).where(m.PartnerCredential.code == code.upper()))
    if not c:
        raise HTTPException(404, "No credential with that code")
    d = _cred(c)
    return {k: d[k] for k in ("issuer", "title", "evidence_url", "issued_on", "revoked", "note")}


# ---------------------------------------------------------------- capability profile and personal learning plan
def _band(attempts: int, accuracy: float | None) -> str:
    if attempts < 3 or accuracy is None:
        return "just starting"
    return "needs practice" if accuracy < 50 else "building" if accuracy < 75 else "steady" if accuracy < 90 else "strong"


@router.get("/me/capability")
def capability(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Per-area picture built from the student's own practice. Deliberately no overall score and no ranking."""
    rows = db.scalars(select(m.TopicProgress).where(m.TopicProgress.user_id == user.id)).all()
    areas: dict[str, list] = {}
    for r in rows:
        acc = round(r.correct / r.attempts * 100) if r.attempts else None
        areas.setdefault(r.pillar, []).append({"topic": r.topic, "attempts": r.attempts, "accuracy": acc, "level": r.level, "band": _band(r.attempts, acc)})
    from ..meta import PILLARS
    out, plan = [], []
    for pillar, topics in sorted(areas.items()):
        att = sum(t["attempts"] for t in topics)
        cor = sum(round((t["accuracy"] or 0) * t["attempts"] / 100) for t in topics)
        acc = round(cor / att * 100) if att else None
        out.append({"pillar": pillar, "name": PILLARS.get(pillar, pillar), "attempts": att, "band": _band(att, acc), "topics": topics})
        for t in topics:
            if t["band"] in ("needs practice", "building"):
                les = db.scalars(select(m.Lesson).where(m.Lesson.status == PUB, m.Lesson.pillar == pillar)
                                 .order_by((m.Lesson.track == t["topic"]).desc(), m.Lesson.level).limit(2)).all()
                plan.append({"pillar": pillar, "topic": t["topic"], "band": t["band"], "next": "Practise this topic again, then read the lessons below.",
                             "lessons": [{"slug": x.slug, "title": x.title, "minutes": x.minutes} for x in les]})
    plan.sort(key=lambda x: (x["band"] != "needs practice", x["pillar"], x["topic"]))
    untouched = [{"pillar": p, "name": n} for p, n in PILLARS.items() if p not in areas][:8]
    return {"areas": out, "plan": plan[:12], "not_started": untouched,
            "note": "This comes only from questions you answered here. It is practice feedback, not a certificate, and there is no overall score. Retake any topic any time."}


# ---------------------------------------------------------------- growth dashboard and promotion readiness
GROWTH_SECTIONS = ["workplace_win", "feedback_received", "responsibility", "promotion", "workplace_learning",
                   "plan_30_60_90", "kpi_okr", "promotion_check", "six_month_review", "leadership_log"]


@router.get("/me/growth-summary")
def growth_summary(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Private. A checklist of what is on record, not a score and not a prediction of a promotion."""
    rows = db.scalars(select(m.MasterEntry).where(m.MasterEntry.user_id == user.id, m.MasterEntry.section.in_(GROWTH_SECTIONS))).all()
    count = {s: sum(1 for r in rows if r.section == s) for s in GROWTH_SECTIONS}
    now = utcnow()
    recent = lambda s, days: any((now - r.created_at).days <= days for r in rows if r.section == s)  # noqa: E731
    month: dict[str, int] = {}
    for r in rows:
        k = r.created_at.strftime("%Y-%m")
        month[k] = month.get(k, 0) + 1
    checks = [
        ("A written 30-60-90 day plan", count["plan_30_60_90"] > 0),
        ("Goals, KPIs or OKRs you can point to", count["kpi_okr"] > 0),
        ("At least three recorded wins", count["workplace_win"] >= 3),
        ("Feedback you have received, good or critical", count["feedback_received"] > 0),
        ("Responsibilities you took on beyond the role", count["responsibility"] > 0),
        ("Something learned at work in the last six months", recent("workplace_learning", 183)),
        ("A review of the last six months", recent("six_month_review", 183)),
        ("A conversation about promotion readiness noted down", count["promotion_check"] > 0),
    ]
    return {"counts": count, "by_month": dict(sorted(month.items())[-12:]),
            "checklist": [{"item": a, "done": d} for a, d in checks],
            "note": "A record to prepare for appraisals and promotion talks. It does not predict a promotion or a raise, and it is never shared with an employer."}


# ---------------------------------------------------------------- practical tools directory (Jugaad Lab)
@router.get("/practical-tools")
def practical_tools(category: str | None = Query(None, max_length=40), db: Session = Depends(get_db)):
    stmt = select(m.PracticalTool).where(m.PracticalTool.status == PUB)
    if category:
        stmt = stmt.where(m.PracticalTool.category == category)
    rows = db.scalars(stmt.order_by(m.PracticalTool.category, m.PracticalTool.name)).all()
    return {"results": [{"slug": r.slug, "name": r.name, "category": r.category, "what_for": r.what_for, "free_option": r.free_option,
                         "paid_details": r.paid_details, "url": r.url, "learn_url": r.learn_url, "provenance": provenance(r)} for r in rows],
            "note": "Plans and prices change often. Check the official page before relying on any detail here."}


# ---------------------------------------------------------------- voluntary pay reports (ranges only, groups of ten or more)
class SalaryIn(BaseModel):
    role_title: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    kind: str = Field(pattern="^(full_time|internship_stipend)$")
    years_experience: int = Field(ge=0, le=45)
    annual_amount: int = Field(ge=0, le=100_000_000)


@router.post("/me/salary-reports", status_code=201)
def add_salary(body: SalaryIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    key = re.sub(r"\s+", " ", body.role_title.strip().lower())
    city = body.city.strip().title()
    if db.scalar(select(m.SalaryReport.id).where(m.SalaryReport.user_id == user.id, m.SalaryReport.role_key == key,
                                                 m.SalaryReport.city == city, m.SalaryReport.kind == body.kind)):
        raise HTTPException(409, "You already added a figure for this role, city and kind. Delete it first to change it.")
    row = m.SalaryReport(user_id=user.id, role_key=key, role_title=body.role_title.strip(), city=city, kind=body.kind,
                         years_experience=body.years_experience, annual_amount=body.annual_amount)
    db.add(row)
    db.commit()
    return {"id": row.id, "note": "Thank you. Your figure is never shown alone or with your name. It only appears inside a range once ten or more people report for the same role."}


@router.get("/me/salary-reports")
def my_salary(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.SalaryReport).where(m.SalaryReport.user_id == user.id).order_by(m.SalaryReport.id.desc())).all()
    return {"results": [{"id": r.id, "role_title": r.role_title, "city": r.city, "kind": r.kind, "annual_amount": r.annual_amount} for r in rows]}


@router.delete("/me/salary-reports/{rid}", status_code=204)
def del_salary(rid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(m.SalaryReport, rid)
    if r is None or r.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(r)
    db.commit()


@router.get("/salary-ranges")
def salary_ranges(role: str | None = Query(None, max_length=120), db: Session = Depends(get_db)):
    """Only ranges (25th to 75th percentile), only for groups of K_MIN or more, always labelled self-reported."""
    stmt = select(m.SalaryReport.role_key, m.SalaryReport.kind).group_by(m.SalaryReport.role_key, m.SalaryReport.kind).having(func.count() >= K_MIN)
    if role:
        stmt = stmt.where(m.SalaryReport.role_key.ilike(f"%{role.strip().lower().replace('%', '').replace('_', '')}%"))
    out = []
    for key, kind in db.execute(stmt.limit(100)).all():
        vals = sorted(db.scalars(select(m.SalaryReport.annual_amount).where(m.SalaryReport.role_key == key, m.SalaryReport.kind == kind)).all())
        n = len(vals)
        title = db.scalar(select(m.SalaryReport.role_title).where(m.SalaryReport.role_key == key).limit(1))
        out.append({"role": title, "kind": kind, "reports": n, "range_low": vals[n // 4], "range_high": vals[(3 * n) // 4],
                    "basis": "Middle half of voluntary self-reported figures"})
    return {"results": out, "note": "Self-reported, unverified, and not a guide to what you will be offered. Pay depends on employer, city, skills and negotiation. Groups under ten are never shown."}


# ---------------------------------------------------------------- peer feedback and retrospectives
class FeedbackReqIn(BaseModel):
    context: str = Field(min_length=3, max_length=200)


class FeedbackGiveIn(BaseModel):
    strengths: str = Field(min_length=3, max_length=600)
    improve: str = Field(min_length=3, max_length=600)


@router.post("/me/feedback-requests", status_code=201)
def new_feedback_request(body: FeedbackReqIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if (db.scalar(select(func.count()).select_from(m.FeedbackRequest).where(m.FeedbackRequest.user_id == user.id)) or 0) >= 20:
        raise HTTPException(409, "You have 20 requests already. Delete one first.")
    r = m.FeedbackRequest(user_id=user.id, token=secrets.token_urlsafe(24), context=body.context.strip())
    db.add(r)
    db.commit()
    return {"id": r.id, "token": r.token, "share_path": f"/connect/feedback/{r.token}"}


@router.get("/me/feedback-requests")
def my_feedback(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for r in db.scalars(select(m.FeedbackRequest).where(m.FeedbackRequest.user_id == user.id).order_by(m.FeedbackRequest.id.desc())).all():
        notes = db.scalars(select(m.FeedbackNote).where(m.FeedbackNote.request_id == r.id).order_by(m.FeedbackNote.id)).all()
        shown = len(notes) >= 3  # fewer than three would make the giver easy to guess
        out.append({"id": r.id, "context": r.context, "share_path": f"/connect/feedback/{r.token}", "closed": r.closed, "count": len(notes),
                    "notes": [{"strengths": n.strengths, "improve": n.improve} for n in notes] if shown else [],
                    "note": None if shown else "Feedback appears once at least three people have replied, so no one can guess who said what."})
    return {"results": out}


@router.delete("/me/feedback-requests/{rid}", status_code=204)
def del_feedback(rid: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(m.FeedbackRequest, rid)
    if r is None or r.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(r)
    db.commit()


@router.get("/me/feedback-give/{token}")
def feedback_context(token: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.scalar(select(m.FeedbackRequest).where(m.FeedbackRequest.token == token))
    if r is None or r.closed:
        raise HTTPException(404, "This feedback request is not available")
    return {"context": r.context, "own": r.user_id == user.id,
            "guide": "Be specific and kind. Describe what you saw, not what you think of the person. The reply is private and shown without your name."}


@router.post("/me/feedback-give/{token}", status_code=201)
def feedback_give(token: str, body: FeedbackGiveIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.scalar(select(m.FeedbackRequest).where(m.FeedbackRequest.token == token))
    if r is None or r.closed:
        raise HTTPException(404, "This feedback request is not available")
    if r.user_id == user.id:
        raise HTTPException(409, "You cannot give feedback on your own request")
    if db.scalar(select(m.FeedbackNote.id).where(m.FeedbackNote.request_id == r.id, m.FeedbackNote.giver_id == user.id)):
        raise HTTPException(409, "You have already replied")
    db.add(m.FeedbackNote(request_id=r.id, giver_id=user.id, strengths=body.strengths.strip(), improve=body.improve.strip()))
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- career relevance radar
@router.get("/me/radar/{role_slug}")
def radar(role_slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """For one published role: how much of each requirement tier you have ticked, and ticked items not revisited for a year."""
    role = db.scalar(select(m.Role).where(m.Role.slug == role_slug, m.Role.status == PUB))
    if role is None:
        raise HTTPException(404, "Role not found")
    reqs = db.scalars(select(m.RoleRequirement).where(m.RoleRequirement.role_id == role.id)).all()
    prog = {p.requirement_id: p for p in db.scalars(select(m.ChecklistProgress).where(
        m.ChecklistProgress.user_id == user.id, m.ChecklistProgress.requirement_id.in_([r.id for r in reqs] or [0])))}
    now = utcnow()
    tiers, refresh = {}, []
    for r in reqs:
        t = tiers.setdefault(r.tier.value, {"tier": r.tier.value, "total": 0, "done": 0})
        t["total"] += 1
        p = prog.get(r.id)
        if p and p.status == m.ProgressStatus.done:
            t["done"] += 1
            if (now - p.updated_at).days > 365:
                refresh.append({"label": r.label, "tier": r.tier.value})
    order = ["mandatory", "common_preference", "recommended", "differentiator"]
    return {"role": {"slug": role.slug, "title": role.title}, "tiers": [tiers[k] for k in order if k in tiers], "refresh": refresh,
            "note": "Requirements change with employers and over time. Ticks older than a year are listed so you can check they are still current. This is a prompt to look again, not a score."}

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import admin_only, editor_or_above, reviewer_or_above
from ..services import curation as cur

router = APIRouter(prefix="/v1/admin", tags=["curation"])


@router.get("/stale")
def stale(db: Session = Depends(get_db), _: m.User = Depends(editor_or_above)):
    """Published facts older than the refresh window, oldest first."""
    return sorted(cur.stale_items(db), key=lambda i: i["last_verified"] or "")


@router.get("/queue")
def review_queue(db: Session = Depends(get_db), _: m.User = Depends(reviewer_or_above)):
    out = []
    for name, (model, _f) in cur.REVIEWABLE.items():
        for r in db.scalars(select(model).where(model.status == m.Status.in_review)):
            out.append({"type": name, "id": r.id, "created_by_id": r.created_by_id,
                        "label": getattr(r, "title", None) or getattr(r, "name", None)
                        or getattr(r, "headline", None) or getattr(r, "degree", None)})
    return out


@router.post("/sources", status_code=201)
def create_source(body: dict = Body(...), db: Session = Depends(get_db), user: m.User = Depends(editor_or_above)):
    allowed = {"url", "title", "publisher", "kind", "published_on"}
    clean = cur._clean(m.Source, allowed, body, creating=True)
    src = m.Source(**clean)
    db.add(src)
    cur._flush(db)
    cur.audit(db, user, "create", "sources", src.id)
    db.commit()
    return cur.serialize(src)


@router.get("/sources")
def list_sources(db: Session = Depends(get_db), _: m.User = Depends(editor_or_above)):
    return [cur.serialize(s) for s in db.scalars(select(m.Source).order_by(m.Source.id.desc()).limit(500))]


@router.get("/reports")
def reports(status: str = "open", db: Session = Depends(get_db), _: m.User = Depends(editor_or_above)):
    rows = db.scalars(select(m.ProblemReport).where(m.ProblemReport.status == m.ReportStatus(status))
                      .order_by(m.ProblemReport.created_at)).all()
    return [cur.serialize(r) for r in rows]


@router.post("/reports/{report_id}/resolve")
def resolve_report(report_id: int, body: dict = Body(default={}), db: Session = Depends(get_db),
                   user: m.User = Depends(editor_or_above)):
    r = db.get(m.ProblemReport, report_id)
    if r is None:
        raise HTTPException(404, "Not found")
    status = body.get("status", "resolved")
    if status not in ("resolved", "dismissed"):
        raise HTTPException(422, "status must be resolved or dismissed")
    r.status, r.resolved_by_id = m.ReportStatus(status), user.id
    r.resolution_note = str(body.get("note", ""))[:1000] or None
    cur.audit(db, user, status, "problem_reports", r.id)
    db.commit()
    return cur.serialize(r)


@router.get("/unanswered")
def unanswered(db: Session = Depends(get_db), _: m.User = Depends(editor_or_above)):
    """Questions students asked that the knowledge base could not answer: the content to-do list."""
    rows = db.scalars(select(m.UnansweredQuestion).where(m.UnansweredQuestion.handled.is_(False))
                      .order_by(m.UnansweredQuestion.times_asked.desc(), m.UnansweredQuestion.last_asked.desc())
                      .limit(200)).all()
    return [{"id": r.id, "question": r.example, "times_asked": r.times_asked, "last_asked": r.last_asked.isoformat()}
            for r in rows]


@router.post("/unanswered/{qid}/handled")
def unanswered_handled(qid: int, db: Session = Depends(get_db), user: m.User = Depends(editor_or_above)):
    r = db.get(m.UnansweredQuestion, qid)
    if r is None:
        raise HTTPException(404, "Not found")
    r.handled = True
    cur.audit(db, user, "handled", "unanswered_questions", r.id)
    db.commit()
    return {"id": r.id, "handled": True}


@router.get("/participation")
def participation(db: Session = Depends(get_db), _: m.User = Depends(admin_only)):
    rows = db.scalars(select(m.ParticipationInterest).where(m.ParticipationInterest.handled.is_(False))
                      .order_by(m.ParticipationInterest.created_at.desc()).limit(200)).all()
    return [{"id": r.id, "pathway": r.pathway, "name": r.name, "organisation": r.organisation, "contact": r.contact,
             "message": r.message, "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/participation/{pid}/handled")
def participation_handled(pid: int, db: Session = Depends(get_db), user: m.User = Depends(admin_only)):
    r = db.get(m.ParticipationInterest, pid)
    if r is None:
        raise HTTPException(404, "Not found")
    r.handled = True
    cur.audit(db, user, "handled", "participation_interests", r.id)
    db.commit()
    return {"id": r.id, "handled": True}


@router.post("/users/{user_id}/role")
def set_role(user_id: int, body: dict = Body(...), db: Session = Depends(get_db), admin: m.User = Depends(admin_only)):
    try:
        role = m.UserRole(body.get("role"))
    except ValueError:
        raise HTTPException(422, "Unknown role")
    u = db.get(m.User, user_id)
    if u is None:
        raise HTTPException(404, "Not found")
    u.role = role
    cur.audit(db, admin, "set_role", "users", u.id, {"role": role.value})
    db.commit()
    return {"id": u.id, "role": u.role.value}


@router.get("/{name}")
def list_items(name: str, status: str | None = None, db: Session = Depends(get_db),
               _: m.User = Depends(editor_or_above)):
    model, _allowed, reviewable = cur.get_entry(name)
    q = select(model).order_by(model.id.desc()).limit(500)
    if status and reviewable:
        q = q.where(model.status == m.Status(status))
    return [cur.serialize(r) for r in db.scalars(q)]


@router.get("/{name}/{obj_id}")
def get_item(name: str, obj_id: int, db: Session = Depends(get_db), _: m.User = Depends(editor_or_above)):
    model, _allowed, _r = cur.get_entry(name)
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Not found")
    return cur.serialize(obj)


@router.post("/{name}", status_code=201)
def create_item(name: str, body: dict = Body(...), db: Session = Depends(get_db),
                user: m.User = Depends(editor_or_above)):
    return cur.serialize(cur.create(db, user, name, body))


@router.patch("/{name}/{obj_id}")
def update_item(name: str, obj_id: int, body: dict = Body(...), db: Session = Depends(get_db),
                user: m.User = Depends(editor_or_above)):
    return cur.serialize(cur.update(db, user, name, obj_id, body))


@router.delete("/{name}/{obj_id}", status_code=204)
def delete_item(name: str, obj_id: int, db: Session = Depends(get_db), user: m.User = Depends(editor_or_above)):
    cur.delete(db, user, name, obj_id)


@router.post("/{name}/{obj_id}/{action}")
def transition(name: str, obj_id: int, action: str, body: dict = Body(default={}), db: Session = Depends(get_db),
               user: m.User = Depends(editor_or_above)):
    return cur.serialize(cur.transition(db, user, name, obj_id, action, body.get("note")))

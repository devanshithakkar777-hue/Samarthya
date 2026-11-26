from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from ..deps import current_user
from ..schemas import ProfileIn, ProgressIn, SaveIn
from ..services.curation import REVIEWABLE
from ..services.fit import compute_fit

router = APIRouter(prefix="/v1/me", tags=["me"])


def _profile_out(db: Session, user: m.User) -> dict:
    p = user.profile
    qual = db.get(m.Qualification, p.qualification_id) if p and p.qualification_id else None
    return {"qualification": qual.slug if qual else None, "year_of_study": p.year_of_study if p else None,
            "expected_graduation_year": p.expected_graduation_year if p else None,
            "interests": p.interests if p else [], "skills": p.skills if p else []}


@router.get("")
def me(user: m.User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role.value, "created_at": user.created_at.isoformat()}


@router.get("/profile")
def get_profile(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return _profile_out(db, user)


@router.put("/profile")
def put_profile(body: ProfileIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    qual_id = None
    if body.qualification:
        q = db.scalar(select(m.Qualification).where(m.Qualification.slug == body.qualification,
                                                    m.Qualification.status == m.Status.published))
        if q is None:
            raise HTTPException(422, "Unknown degree")
        qual_id = q.id
    p = user.profile or m.Profile(user_id=user.id)
    p.qualification_id, p.year_of_study = qual_id, body.year_of_study
    p.expected_graduation_year = body.expected_graduation_year
    p.interests, p.skills = body.interests, body.skills
    db.add(p)
    db.commit()
    db.refresh(user)
    return _profile_out(db, user)


def _completed(db: Session, user: m.User) -> list[int]:
    return list(db.scalars(select(m.ChecklistProgress.requirement_id).where(
        m.ChecklistProgress.user_id == user.id, m.ChecklistProgress.status == m.ProgressStatus.done)))


@router.get("/fit")
def my_fit(sort: str = "eligibility", user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if sort not in ("eligibility", "compatibility", "readiness"):
        raise HTTPException(422, "Unknown sort")
    p = _profile_out(db, user)
    return {"results": compute_fit(db, p["qualification"], p["year_of_study"], p["interests"], p["skills"],
                                   _completed(db, user), sort)}


@router.get("/checklist/{role_slug}")
def my_checklist(role_slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    role = db.scalar(select(m.Role).where(m.Role.slug == role_slug, m.Role.status == m.Status.published)
                     .options(selectinload(m.Role.requirements)))
    if role is None:
        raise HTTPException(404, "Not found")
    prog = {p.requirement_id: p.status.value for p in db.scalars(
        select(m.ChecklistProgress).where(m.ChecklistProgress.user_id == user.id))}
    return {"role": {"slug": role.slug, "title": role.title},
            "items": [{"id": r.id, "label": r.label, "tier": r.tier.value, "type": r.type.value,
                       "status": prog.get(r.id, "todo")} for r in role.requirements]}


@router.put("/checklist/items/{requirement_id}")
def set_progress(requirement_id: int, body: ProgressIn, user: m.User = Depends(current_user),
                 db: Session = Depends(get_db)):
    req = db.get(m.RoleRequirement, requirement_id)
    if req is None or req.role.status != m.Status.published:
        raise HTTPException(404, "Not found")
    row = db.get(m.ChecklistProgress, (user.id, requirement_id))
    if row is None:
        row = m.ChecklistProgress(user_id=user.id, requirement_id=requirement_id)
    row.status = m.ProgressStatus(body.status)
    db.add(row)
    db.commit()
    return {"id": requirement_id, "status": body.status}


@router.get("/saved")
def saved(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.SavedItem).where(m.SavedItem.user_id == user.id)
                      .order_by(m.SavedItem.created_at.desc())).all()
    return [{"entity_type": r.entity_type, "entity_id": r.entity_id} for r in rows]


@router.post("/saved", status_code=201)
def save(body: SaveIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    exists = db.scalar(select(m.SavedItem).where(m.SavedItem.user_id == user.id,
                                                 m.SavedItem.entity_type == body.entity_type,
                                                 m.SavedItem.entity_id == body.entity_id))
    if exists is None:
        db.add(m.SavedItem(user_id=user.id, entity_type=body.entity_type, entity_id=body.entity_id))
        db.commit()
    return {"saved": True}


@router.delete("/saved/{entity_type}/{entity_id}", status_code=204)
def unsave(entity_type: str, entity_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(m.SavedItem).where(m.SavedItem.user_id == user.id, m.SavedItem.entity_type == entity_type,
                                         m.SavedItem.entity_id == entity_id))
    db.commit()


@router.get("/export")
def export(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Everything stored about the signed-in student."""
    return {"account": {"email": user.email, "created_at": user.created_at.isoformat()},
            "profile": _profile_out(db, user),
            "checklist": [{"requirement_id": p.requirement_id, "status": p.status.value}
                          for p in db.scalars(select(m.ChecklistProgress).where(m.ChecklistProgress.user_id == user.id))],
            "saved": [{"entity_type": s.entity_type, "entity_id": s.entity_id}
                      for s in db.scalars(select(m.SavedItem).where(m.SavedItem.user_id == user.id))]}


@router.delete("", status_code=204)
def delete_account(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Permanently removes the account and everything attached to it."""
    db.execute(delete(m.OtpCode).where(m.OtpCode.email == user.email))
    for model in (m.ChecklistProgress, m.SavedItem):
        db.execute(delete(model).where(model.user_id == user.id))
    db.execute(delete(m.Profile).where(m.Profile.user_id == user.id))
    # content the account authored keeps its history but loses the link to the person
    for model, _f in REVIEWABLE.values():
        db.execute(model.__table__.update().where(model.created_by_id == user.id).values(created_by_id=None))
        db.execute(model.__table__.update().where(model.reviewed_by_id == user.id).values(reviewed_by_id=None))
    db.execute(m.AuditLog.__table__.update().where(m.AuditLog.user_id == user.id).values(user_id=None))
    db.execute(m.ProblemReport.__table__.update().where(m.ProblemReport.resolved_by_id == user.id)
               .values(resolved_by_id=None))
    db.delete(user)
    db.commit()

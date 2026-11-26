from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..deps import RateLimiter
from ..schemas import ParticipateIn, ReportIn

router = APIRouter(prefix="/v1", tags=["reports"])
report_limit = RateLimiter(limit=10, window_seconds=3600)


@router.post("/reports", status_code=201, dependencies=[Depends(report_limit)])
def create_report(body: ReportIn, db: Session = Depends(get_db)):
    r = m.ProblemReport(entity_type=body.entity_type, entity_id=body.entity_id, page_url=body.page_url,
                        message=body.message.strip(), contact=body.contact)
    db.add(r)
    db.commit()
    return {"id": r.id, "message": "Thank you. An editor will review this."}


participate_limit = RateLimiter(limit=5, window_seconds=3600)


@router.post("/participate", status_code=201, dependencies=[Depends(participate_limit)])
def participate(body: ParticipateIn, db: Session = Depends(get_db)):
    db.add(m.ParticipationInterest(pathway=body.pathway, name=body.name, organisation=body.organisation,
                                   contact=str(body.contact).lower(), message=(body.message or "").strip() or None))
    db.commit()
    return {"message": "Thank you. We will be in touch by email."}

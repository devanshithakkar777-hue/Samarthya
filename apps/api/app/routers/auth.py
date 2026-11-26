from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import RateLimiter
from ..schemas import OtpRequestIn, OtpVerifyIn
from ..security import create_token
from ..services import otp

router = APIRouter(prefix="/v1/auth", tags=["auth"])
auth_limit = RateLimiter(limit=20, window_seconds=3600)


@router.post("/otp/request", dependencies=[Depends(auth_limit)], status_code=202)
def request_code(body: OtpRequestIn, db: Session = Depends(get_db)):
    try:
        otp.request_code(db, body.email)
    except otp.OtpError as e:
        raise HTTPException(e.status, e.message)
    return {"message": "If that address can receive mail, a code is on its way."}


@router.post("/otp/verify", dependencies=[Depends(auth_limit)])
def verify_code(body: OtpVerifyIn, db: Session = Depends(get_db)):
    try:
        user = otp.verify_code(db, body.email, body.code)
    except otp.OtpError as e:
        raise HTTPException(e.status, e.message)
    return {"token": create_token(user), "user": {"email": user.email, "role": user.role.value}}

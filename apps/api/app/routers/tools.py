"""Public tools that need no account and store nothing."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from fastapi import HTTPException

from ..services import interests, scam

router = APIRouter(prefix="/v1/tools", tags=["tools"])


class ScamIn(BaseModel):
    text: str = Field(min_length=10, max_length=6000)


@router.post("/scam-check")
def scam_check(body: ScamIn):
    return scam.check(body.text)


class InterestIn(BaseModel):
    answers: list[int] = Field(min_length=36, max_length=36)


@router.get("/interests")
def interest_items():
    return interests.items()


@router.post("/interests")
def interest_score(body: InterestIn):
    try:
        return interests.score(body.answers)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

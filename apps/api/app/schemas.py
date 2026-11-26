from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

SLUG = r"^[a-z0-9][a-z0-9-]{0,99}$"


class ProfileIn(BaseModel):
    qualification: str | None = Field(default=None, pattern=SLUG)
    year_of_study: int | None = Field(default=None, ge=1, le=6)
    expected_graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    interests: list[str] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=60)

    @field_validator("interests", "skills")
    @classmethod
    def _slugs(cls, v: list[str]) -> list[str]:
        import re

        for item in v:
            if not re.match(SLUG, item):
                raise ValueError("entries must be lowercase slugs")
        return list(dict.fromkeys(v))


class FitRequest(BaseModel):
    profile: ProfileIn
    completed_requirement_ids: list[int] = Field(default_factory=list, max_length=1000)
    sort: Literal["eligibility", "compatibility", "readiness"] = "eligibility"


class OtpRequestIn(BaseModel):
    email: EmailStr


class OtpVerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ProgressIn(BaseModel):
    status: Literal["todo", "doing", "done"]


class SaveIn(BaseModel):
    entity_type: Literal["role", "company", "sector", "skill"]
    entity_id: int


class ReportIn(BaseModel):
    entity_type: Literal["sector", "role", "company", "skill", "resource", "roadmap_step", "news", "page"] | None = None
    entity_id: int | None = None
    page_url: str | None = Field(default=None, max_length=500)
    message: str = Field(min_length=10, max_length=2000)
    contact: EmailStr | None = None


class ParticipateIn(BaseModel):
    pathway: Literal["mentor", "contribute", "institution", "volunteer", "other"]
    name: str | None = Field(default=None, max_length=120)
    organisation: str | None = Field(default=None, max_length=160)
    contact: EmailStr
    message: str | None = Field(default=None, max_length=2000)

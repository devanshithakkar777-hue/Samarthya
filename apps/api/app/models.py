"""Data model for the Samarthya careers core.

Rules baked into the schema (see the strategy doc, "Rules for the knowledge base"):
- every reviewable fact has a source and a last-verified date before it can be published;
- requirements are tagged by tier so a nice-to-have is never mistaken for a rule;
- the public API only ever reads published rows.
"""
import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from .db import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum(e: type[enum.Enum], name: str):
    return Enum(e, name=name, native_enum=False, create_constraint=True, length=32,
                values_callable=lambda x: [m.value for m in x])


class Status(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"


class SourceKind(str, enum.Enum):
    official = "official"
    open_data = "open_data"
    licensed = "licensed"
    third_party = "third_party"


class RequirementType(str, enum.Enum):
    skill = "skill"
    subject = "subject"
    internship = "internship"
    experience = "experience"
    certification = "certification"


class Tier(str, enum.Enum):
    mandatory = "mandatory"
    common_preference = "common_preference"
    recommended = "recommended"
    differentiator = "differentiator"


class UserRole(str, enum.Enum):
    student = "student"
    editor = "editor"
    reviewer = "reviewer"
    admin = "admin"


class ProgressStatus(str, enum.Enum):
    todo = "todo"
    doing = "doing"
    done = "done"


class ReportStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(200))
    kind: Mapped[SourceKind] = mapped_column(_enum(SourceKind, "source_kind"))
    published_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Reviewable:
    """Mixin for content that goes through draft, review and publish."""

    status: Mapped[Status] = mapped_column(_enum(Status, "content_status"), default=Status.draft, index=True)
    last_verified: Mapped[date | None] = mapped_column(Date)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @declared_attr
    def source_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("sources.id"), nullable=True)

    @declared_attr
    def created_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), nullable=True)

    @declared_attr
    def reviewed_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), nullable=True)


class Qualification(Reviewable, Base):
    __tablename__ = "qualifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    degree: Mapped[str] = mapped_column(String(120))
    level: Mapped[str] = mapped_column(String(40))  # e.g. undergraduate, postgraduate
    specialization: Mapped[str | None] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(40), default="degree", server_default="degree")  # degree, diploma, certificate, professional_qualification, certification, licence, examination
    stream: Mapped[str | None] = mapped_column(String(80))  # one of the discovery streams; a degree can be reached from several, this is the primary
    awarding_body: Mapped[str | None] = mapped_column(String(160))
    eligibility: Mapped[str | None] = mapped_column(Text)
    entry_route: Mapped[str | None] = mapped_column(Text)
    training: Mapped[str | None] = mapped_column(Text)
    recognition: Mapped[str | None] = mapped_column(Text)
    cost_note: Mapped[str | None] = mapped_column(Text)
    official_url: Mapped[str | None] = mapped_column(String(300))
    duration_years: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None when the source does not state it
    source = relationship("Source")


class Sector(Reviewable, Base):
    __tablename__ = "sectors"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    source = relationship("Source")


class QualificationSector(Base):
    """Which education opens which sectors, with a reason and a source."""

    __tablename__ = "qualification_sectors"
    __table_args__ = (
        UniqueConstraint("qualification_id", "sector_id"),
        CheckConstraint("strength between 1 and 3", name="ck_qs_strength"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    qualification_id: Mapped[int] = mapped_column(ForeignKey("qualifications.id", ondelete="CASCADE"))
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"))
    strength: Mapped[int] = mapped_column(Integer, default=2)  # 1 possible, 2 common, 3 direct
    reason: Mapped[str] = mapped_column(Text)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    last_verified: Mapped[date] = mapped_column(Date)
    qualification = relationship("Qualification")
    sector = relationship("Sector")
    source = relationship("Source")


class Role(Reviewable, Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    job_family: Mapped[str] = mapped_column(String(120))
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"))
    level: Mapped[str] = mapped_column(String(40), default="entry")
    description: Mapped[str] = mapped_column(Text)
    progression: Mapped[str | None] = mapped_column(Text)
    sector = relationship("Sector")
    source = relationship("Source")
    requirements = relationship("RoleRequirement", back_populates="role", cascade="all, delete-orphan",
                                order_by="RoleRequirement.position")
    qualifications = relationship("RoleQualification", cascade="all, delete-orphan")
    hiring = relationship("CompanyRole", back_populates="role", cascade="all, delete-orphan")


class RoleQualification(Base):
    """Degrees the role lists as an entry route. No rows means no degree is specified."""

    __tablename__ = "role_qualifications"
    __table_args__ = (UniqueConstraint("role_id", "qualification_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    qualification_id: Mapped[int] = mapped_column(ForeignKey("qualifications.id", ondelete="CASCADE"))
    note: Mapped[str | None] = mapped_column(String(300))
    qualification = relationship("Qualification")


class Skill(Reviewable, Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80))
    overview: Mapped[str] = mapped_column(Text)
    source = relationship("Source")
    resources = relationship("LearningResource", back_populates="skill")


class RoleRequirement(Base):
    __tablename__ = "role_requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    type: Mapped[RequirementType] = mapped_column(_enum(RequirementType, "requirement_type"))
    tier: Mapped[Tier] = mapped_column(_enum(Tier, "requirement_tier"))
    label: Mapped[str] = mapped_column(String(240))
    note: Mapped[str | None] = mapped_column(Text)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    role = relationship("Role", back_populates="requirements")
    skill = relationship("Skill")


class Company(Reviewable, Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    cin: Mapped[str | None] = mapped_column(String(30))
    listing_status: Mapped[str | None] = mapped_column(String(40))
    industry_code: Mapped[str | None] = mapped_column(String(30))
    summary: Mapped[str] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(500))
    source = relationship("Source")
    hiring = relationship("CompanyRole", back_populates="company", cascade="all, delete-orphan")


class CompanyRole(Base):
    __tablename__ = "company_roles"
    __table_args__ = (UniqueConstraint("company_id", "role_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    careers_url: Mapped[str] = mapped_column(String(2048))
    last_verified: Mapped[date] = mapped_column(Date)
    company = relationship("Company", back_populates="hiring")
    role = relationship("Role", back_populates="hiring")


class LearningResource(Reviewable, Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    provider: Mapped[str] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(String(2048))
    format: Mapped[str] = mapped_column(String(40))
    level: Mapped[str] = mapped_column(String(40))
    price_inr: Mapped[int] = mapped_column(Integer, default=0)  # 0 means free
    language: Mapped[str] = mapped_column(String(40), default="English")
    duration_hours: Mapped[int | None] = mapped_column(Integer)
    certificate: Mapped[bool] = mapped_column(Boolean, default=False)
    sponsored: Mapped[bool] = mapped_column(Boolean, default=False)
    skill = relationship("Skill", back_populates="resources")
    source = relationship("Source")


class RoadmapStep(Reviewable, Base):
    __tablename__ = "roadmap_steps"
    __table_args__ = (CheckConstraint("year_of_study between 1 and 6", name="ck_step_year"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    qualification_id: Mapped[int] = mapped_column(ForeignKey("qualifications.id"), index=True)
    year_of_study: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    qualification = relationship("Qualification")
    source = relationship("Source")


class NewsItem(Reviewable, Base):
    """Basic industry briefing. Written or edited by a person, never published unreviewed."""

    __tablename__ = "news_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    headline: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(String(2048))
    event_date: Mapped[date] = mapped_column(Date)
    sector = relationship("Sector")
    source = relationship("Source")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    role: Mapped[UserRole] = mapped_column(_enum(UserRole, "user_role"), default=UserRole.student)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    profile = relationship("Profile", uselist=False, back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    qualification_id: Mapped[int | None] = mapped_column(ForeignKey("qualifications.id"))
    year_of_study: Mapped[int | None] = mapped_column(Integer)
    expected_graduation_year: Mapped[int | None] = mapped_column(Integer)
    interests: Mapped[list] = mapped_column(JsonType, default=list)  # sector slugs
    skills: Mapped[list] = mapped_column(JsonType, default=list)  # skill slugs the student reports
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    user = relationship("User", back_populates="profile")


class ChecklistProgress(Base):
    __tablename__ = "checklist_progress"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("role_requirements.id", ondelete="CASCADE"),
                                                primary_key=True)
    status: Mapped[ProgressStatus] = mapped_column(_enum(ProgressStatus, "progress_status"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SavedItem(Base):
    __tablename__ = "saved_items"
    __table_args__ = (UniqueConstraint("user_id", "entity_type", "entity_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    __table_args__ = (Index("ix_otp_email_created", "email", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProblemReport(Base):
    __tablename__ = "problem_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    page_url: Mapped[str | None] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text)
    contact: Mapped[str | None] = mapped_column(String(320))
    status: Mapped[ReportStatus] = mapped_column(_enum(ReportStatus, "report_status"), default=ReportStatus.open)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class UnansweredQuestion(Base):
    """Questions Ask could not answer from sourced facts, so editors know what to write next.

    Stores only the question text (trimmed) and a count. No user, IP or session is recorded.
    """
    __tablename__ = "unanswered_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    normalized: Mapped[str] = mapped_column(String(300), unique=True)
    example: Mapped[str] = mapped_column(String(300))
    times_asked: Mapped[int] = mapped_column(Integer, default=1)
    first_asked: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_asked: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    handled: Mapped[bool] = mapped_column(Boolean, default=False)


class ParticipationInterest(Base):
    """Someone offering to help: learn, mentor, contribute, partner or volunteer."""
    __tablename__ = "participation_interests"
    id: Mapped[int] = mapped_column(primary_key=True)
    pathway: Mapped[str] = mapped_column(String(40))
    name: Mapped[str | None] = mapped_column(String(120))
    organisation: Mapped[str | None] = mapped_column(String(160))
    contact: Mapped[str] = mapped_column(String(320))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    handled: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    """Who changed what in the knowledge base. No student data is stored here."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)




from .models_ext import *  # noqa: E402,F401,F403  (registers and re-exports the remaining tables)

"""Data model for the modules beyond the careers core: learn, practise, build, explore, live, connect.

Two kinds of table:
- reviewable content (Reviewable mixin): lessons, library items, questions and so on. Same draft, review,
  publish rules as the careers content: a source and a last-verified date are required to publish.
- student-owned rows: always tied to one account with ON DELETE CASCADE, so deleting the account removes
  them. Nothing here is ever exposed publicly. Wellness journal text is stored encrypted.
"""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .models import JsonType, Reviewable, utcnow


def _uid(index: bool = True):
    return mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=index)


# --------------------------------------------------------------------------- reviewable content
class Lesson(Reviewable, Base):
    """One short lesson in an academy track (English, reasoning, AI literacy, money, leadership...)."""

    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    pillar: Mapped[str] = mapped_column(String(40), index=True)
    track: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="beginner")
    minutes: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(40), default="English")
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    source = relationship("Source")


class LibraryItem(Reviewable, Base):
    """A link to a legally available reading. The platform never hosts or copies the file itself."""

    __tablename__ = "library_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    authors: Mapped[str | None] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(40), index=True)
    subject: Mapped[str] = mapped_column(String(120), index=True)
    stream: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(40), default="English")
    publisher: Mapped[str | None] = mapped_column(String(200))
    access_url: Mapped[str] = mapped_column(String(2048))
    licence_status: Mapped[str] = mapped_column(String(40))
    licence_note: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(20), default="web")
    level: Mapped[str | None] = mapped_column(String(40))
    edition_year: Mapped[int | None] = mapped_column(Integer)
    source = relationship("Source")


class Question(Reviewable, Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    pillar: Mapped[str] = mapped_column(String(40), index=True)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    kind: Mapped[str] = mapped_column(String(10), default="mcq")  # mcq | open
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JsonType, default=list)
    correct_index: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str | None] = mapped_column(Text)
    guidance: Mapped[str | None] = mapped_column(Text)  # what a good answer to an open question covers
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    source = relationship("Source")


class Assessment(Reviewable, Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    pillar: Mapped[str] = mapped_column(String(40), index=True)
    description: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    question_slugs: Mapped[list] = mapped_column(JsonType, default=list)
    credential_type: Mapped[str] = mapped_column(String(20), default="internal")  # internal | partner | accredited
    issuer: Mapped[str | None] = mapped_column(String(200))
    official_url: Mapped[str | None] = mapped_column(String(2048))
    source = relationship("Source")


class Scenario(Reviewable, Base):
    """A branching case or challenge. nodes is a validated graph: see services/scenario.py."""

    __tablename__ = "scenarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    pillar: Mapped[str] = mapped_column(String(40), index=True)  # case, jugaad, crisis, ethics, leadership, ai_vs_human
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    minutes: Mapped[int | None] = mapped_column(Integer)
    brief: Mapped[str] = mapped_column(Text)
    dimensions: Mapped[list] = mapped_column(JsonType, default=list)
    nodes: Mapped[list] = mapped_column(JsonType, default=list)
    real_case: Mapped[bool] = mapped_column(Boolean, default=False)  # documented real event vs constructed exercise
    source = relationship("Source")
    sector = relationship("Sector")


class Opportunity(Reviewable, Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    organisation: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(40), index=True)
    description: Mapped[str] = mapped_column(Text)
    eligibility: Mapped[str] = mapped_column(Text)
    min_year: Mapped[int | None] = mapped_column(Integer)
    max_year: Mapped[int | None] = mapped_column(Integer)
    streams: Mapped[list] = mapped_column(JsonType, default=list)
    skills: Mapped[list] = mapped_column(JsonType, default=list)
    location: Mapped[str | None] = mapped_column(String(160))
    mode: Mapped[str | None] = mapped_column(String(20))
    stipend: Mapped[str | None] = mapped_column(String(160))
    duration_text: Mapped[str | None] = mapped_column(String(120))
    deadline: Mapped[date | None] = mapped_column(Date, index=True)
    rolling: Mapped[bool] = mapped_column(Boolean, default=False)
    selection_process: Mapped[str | None] = mapped_column(Text)
    apply_url: Mapped[str] = mapped_column(String(2048))
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    source = relationship("Source")
    sector = relationship("Sector")


class GlobalBrief(Reviewable, Base):
    """A world event explained the same seven ways every time."""

    __tablename__ = "global_briefs"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    region: Mapped[str | None] = mapped_column(String(80))
    event_date: Mapped[date] = mapped_column(Date, index=True)
    headline: Mapped[str] = mapped_column(String(300))
    what_happened: Mapped[str] = mapped_column(Text)
    what_led: Mapped[str] = mapped_column(Text)
    why_matters: Mapped[str] = mapped_column(Text)
    who_affected: Mapped[str] = mapped_column(Text)
    consequences: Mapped[str] = mapped_column(Text)
    what_next: Mapped[str] = mapped_column(Text)
    investigate: Mapped[str] = mapped_column(Text)
    connects_to: Mapped[list] = mapped_column(JsonType, default=list)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))
    source = relationship("Source")


class Country(Reviewable, Base):
    __tablename__ = "countries"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    iso_numeric: Mapped[str] = mapped_column(String(3), unique=True)
    iso_alpha3: Mapped[str | None] = mapped_column(String(3))
    region: Mapped[str | None] = mapped_column(String(80))
    capital: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    facts: Mapped[list] = mapped_column(JsonType, default=list)  # [{"label": ..., "value": ...}]
    source = relationship("Source")


class TimelineEvent(Reviewable, Base):
    __tablename__ = "timeline_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    event_year: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(80))
    category: Mapped[str | None] = mapped_column(String(60))
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    source = relationship("Source")


class WellnessResource(Reviewable, Base):
    __tablename__ = "wellness_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    kind: Mapped[str] = mapped_column(String(30), index=True)  # helpline, directory, article, exercise, campus
    summary: Mapped[str] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(60))
    url: Mapped[str | None] = mapped_column(String(2048))
    hours: Mapped[str | None] = mapped_column(String(120))
    languages: Mapped[str | None] = mapped_column(String(200))
    cost: Mapped[str | None] = mapped_column(String(40))
    audience: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    source = relationship("Source")


class PracticalTool(Reviewable, Base):
    """A tool worth knowing (Jugaad Lab directory). Prices change, so the page always sends people to the official source."""
    __tablename__ = "practical_tools"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40), index=True)
    what_for: Mapped[str] = mapped_column(Text)
    free_option: Mapped[str | None] = mapped_column(String(300))
    paid_details: Mapped[str | None] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(2048))
    learn_url: Mapped[str | None] = mapped_column(String(2048))
    source = relationship("Source")


# --------------------------------------------------------------------------- student-owned: learn
class UserNote(Base):
    __tablename__ = "user_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    ref_type: Mapped[str | None] = mapped_column(String(30))
    ref_id: Mapped[int | None] = mapped_column(Integer)
    folder: Mapped[str | None] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FlashDeck(Base):
    __tablename__ = "flash_decks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    title: Mapped[str] = mapped_column(String(160))
    subject: Mapped[str | None] = mapped_column(String(120))
    cards = relationship("Flashcard", cascade="all, delete-orphan", back_populates="deck")


class Flashcard(Base):
    """Spaced repetition state (SM-2 style). due is the next day it should be shown."""

    __tablename__ = "flashcards"
    id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("flash_decks.id", ondelete="CASCADE"), index=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    due: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    deck = relationship("FlashDeck", back_populates="cards")


class StudyItem(Base):
    __tablename__ = "study_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    kind: Mapped[str] = mapped_column(String(20))  # revision, assignment, exam, practical, backlog, reading, goal
    title: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str | None] = mapped_column(String(120))
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default="todo")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- student-owned: practise
class TopicProgress(Base):
    __tablename__ = "topic_progress"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    pillar: Mapped[str] = mapped_column(String(40), primary_key=True)
    topic: Mapped[str] = mapped_column(String(120), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    recent: Mapped[list] = mapped_column(JsonType, default=list)  # last results, 1 or 0
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class QuestionResponse(Base):
    __tablename__ = "question_responses"
    __table_args__ = (Index("ix_qr_user_q", "user_id", "question_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    chosen: Mapped[int | None] = mapped_column(Integer)
    correct: Mapped[bool | None] = mapped_column(Boolean)
    answer_text: Mapped[str | None] = mapped_column(Text)
    ratings: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answers: Mapped[dict] = mapped_column(JsonType, default=dict)
    score_pct: Mapped[float | None] = mapped_column(Float)
    per_topic: Mapped[dict] = mapped_column(JsonType, default=dict)
    assessment = relationship("Assessment")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    path: Mapped[list] = mapped_column(JsonType, default=list)
    scores: Mapped[dict] = mapped_column(JsonType, default=dict)
    current: Mapped[str | None] = mapped_column(String(60))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    scenario = relationship("Scenario")


class UserBadge(Base):
    __tablename__ = "user_badges"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    badge_key: Mapped[str] = mapped_column(String(60), primary_key=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ActivityDay(Base):
    """Which days a student did any learning activity. Used only for their own streak, never ranked or shared."""

    __tablename__ = "activity_days"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1)


# --------------------------------------------------------------------------- student-owned: build
class MasterEntry(Base):
    """One item in the master profile. Resumes are assembled from these; nothing is invented."""

    __tablename__ = "master_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    section: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(200))
    organisation: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(120))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    current: Mapped[bool] = mapped_column(Boolean, default=False)
    detail: Mapped[str | None] = mapped_column(String(300))  # grade, role type, publication venue, language level
    bullets: Mapped[list] = mapped_column(JsonType, default=list)
    evidence: Mapped[list] = mapped_column(JsonType, default=list)  # [{kind, url, label}]
    tags: Mapped[list] = mapped_column(JsonType, default=list)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    name: Mapped[str] = mapped_column(String(160))
    target_kind: Mapped[str] = mapped_column(String(30), default="general")
    target_ref: Mapped[str | None] = mapped_column(String(160))  # role/sector/company slug or free text
    job_description: Mapped[str | None] = mapped_column(Text)
    headline: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    contact: Mapped[dict] = mapped_column(JsonType, default=dict)
    selection: Mapped[list] = mapped_column(JsonType, default=list)  # [{entry_id, bullets:[idx], section_order}]
    section_order: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    versions = relationship("ResumeVersion", cascade="all, delete-orphan", back_populates="resume",
                            order_by="ResumeVersion.id.desc()")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    snapshot: Mapped[dict] = mapped_column(JsonType)
    change_note: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resume = relationship("Resume", back_populates="versions")


class DefenceAnswer(Base):
    """A student's practice answer to a question generated from one of their own resume lines."""

    __tablename__ = "defence_answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    entry_id: Mapped[int | None] = mapped_column(Integer)
    topic: Mapped[str] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    self_scores: Mapped[dict] = mapped_column(JsonType, default=dict)
    feedback: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- student-owned: explore
class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(240))
    organisation: Mapped[str | None] = mapped_column(String(200))
    apply_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20), default="saved")
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    deadline: Mapped[date | None] = mapped_column(Date)
    follow_up: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    history: Mapped[list] = mapped_column(JsonType, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    opportunity = relationship("Opportunity")


# --------------------------------------------------------------------------- student-owned: live
class JournalEntry(Base):
    """Private. The text is encrypted at rest and never leaves the account owner's own requests."""

    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    day: Mapped[date] = mapped_column(Date, default=date.today)
    mood: Mapped[int | None] = mapped_column(Integer)
    body_enc: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- connect
class Member(Base):
    """Public community identity. A chosen handle, never the email address."""

    __tablename__ = "members"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    handle: Mapped[str] = mapped_column(String(40), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    board: Mapped[str] = mapped_column(String(40), index=True)
    author_id: Mapped[int] = _uid()
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="visible", index=True)  # visible, hidden, removed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    author = relationship("Member", primaryjoin="Post.author_id==Member.user_id", foreign_keys=[author_id],
                          viewonly=True)
    replies = relationship("Reply", cascade="all, delete-orphan", back_populates="post")


class Reply(Base):
    __tablename__ = "replies"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = _uid()
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="visible")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    post = relationship("Post", back_populates="replies")
    author = relationship("Member", primaryjoin="Reply.author_id==Member.user_id", foreign_keys=[author_id],
                          viewonly=True)


class ContentReport(Base):
    __tablename__ = "content_reports"
    __table_args__ = (UniqueConstraint("reporter_id", "kind", "target_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))  # post | reply | mentor
    target_id: Mapped[int] = mapped_column(Integer, index=True)
    reporter_id: Mapped[int] = _uid()
    reason: Mapped[str] = mapped_column(String(300))
    handled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Mentor(Base):
    __tablename__ = "mentors"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    headline: Mapped[str] = mapped_column(String(200))
    bio: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))  # industry, alumni, academic, research, entrepreneurship
    expertise: Mapped[list] = mapped_column(JsonType, default=list)
    languages: Mapped[list] = mapped_column(JsonType, default=list)
    profile_url: Mapped[str | None] = mapped_column(String(2048))  # public profile a reviewer can check
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)  # pending, approved, paused, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MentorRequest(Base):
    __tablename__ = "mentor_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = _uid()
    mentor_id: Mapped[int] = mapped_column(ForeignKey("mentors.user_id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(Text)
    share_contact: Mapped[str | None] = mapped_column(String(320))  # only if the student chose to include it
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending, accepted, declined, closed
    reply: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="college")
    join_code_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InstitutionStaff(Base):
    __tablename__ = "institution_staff"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default="placement")  # placement, faculty, admin


class InstitutionMember(Base):
    """A student's choice to be counted in their institution's aggregate numbers. Off by default."""

    __tablename__ = "institution_members"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="CASCADE"), primary_key=True)
    share_readiness: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_year: Mapped[int | None] = mapped_column(Integer)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Portfolio(Base):
    """A public page the student chooses to publish from their own master profile. Off until they switch it on."""

    __tablename__ = "portfolios"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    indexable: Mapped[bool] = mapped_column(Boolean, default=False)  # search engines may list it only if the student agrees
    display_name: Mapped[str] = mapped_column(String(120))
    headline: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    entry_ids: Mapped[list] = mapped_column(JsonType, default=list)
    links: Mapped[list] = mapped_column(JsonType, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ParentShare(Base):
    """An opt-in, revocable read-only link a student can give a parent or guardian. Only a hash of the token is stored."""

    __tablename__ = "parent_shares"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str | None] = mapped_column(String(60))
    show_activity: Mapped[bool] = mapped_column(Boolean, default=True)
    show_badges: Mapped[bool] = mapped_column(Boolean, default=True)
    show_topics: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# --------------------------------------------------------------------------- study, practice, mentoring, business
class LibraryNote(Base):
    """A student's own highlight or note on a library item. The platform hosts no book text: the student types
    the short passage and their note themselves, so this is the student's own writing."""

    __tablename__ = "library_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    item_id: Mapped[int] = mapped_column(ForeignKey("library_items.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10), default="note")  # note | highlight
    quote: Mapped[str | None] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConceptMap(Base):
    __tablename__ = "concept_maps"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    title: Mapped[str] = mapped_column(String(160))
    data: Mapped[dict] = mapped_column(JsonType, default=dict)  # {"nodes": [{id,label}], "edges": [{from,to,label}]}
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MockInterview(Base):
    """A practice interview. Turns are the student's own answers plus the feedback shown; private to the student."""

    __tablename__ = "mock_interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    role_slug: Mapped[str | None] = mapped_column(String(100))
    question_slugs: Mapped[list] = mapped_column(JsonType, default=list)
    turns: Mapped[list] = mapped_column(JsonType, default=list)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MentorSession(Base):
    """A group session an approved mentor offers. The mentor adds their own meeting details; the platform hosts no calls."""

    __tablename__ = "mentor_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("mentors.user_id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    minutes: Mapped[int] = mapped_column(Integer, default=45)
    capacity: Mapped[int] = mapped_column(Integer, default=10)
    meeting_details: Mapped[str | None] = mapped_column(String(500))  # shown only to students who joined
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MentorSessionSeat(Base):
    __tablename__ = "mentor_session_seats"
    __table_args__ = (UniqueConstraint("session_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("mentor_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = _uid()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Employer(Base):
    __tablename__ = "employers"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmployerStaff(Base):
    __tablename__ = "employer_staff"
    __table_args__ = (UniqueConstraint("employer_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("employers.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = _uid()


class Venture(Base):
    """A student's own venture or idea tracker (entrepreneurship dashboard). Private."""

    __tablename__ = "ventures"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    name: Mapped[str] = mapped_column(String(160))
    stage: Mapped[str] = mapped_column(String(20), default="idea")  # idea | validating | building | launched
    problem: Mapped[str | None] = mapped_column(Text)
    customer: Mapped[str | None] = mapped_column(Text)
    milestones: Mapped[list] = mapped_column(JsonType, default=list)  # [{text, done}]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PartnerCredential(Base):
    """A credential issued by a named partner organisation and recorded by an admin. Not accredited by Samarthya."""

    __tablename__ = "partner_credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    code: Mapped[str] = mapped_column(String(24), unique=True)
    issuer: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(240))
    evidence_url: Mapped[str] = mapped_column(String(2048))  # the partner's own page or certificate
    recorded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# --------------------------------------------------------------------------- pay reports and peer feedback
class SalaryReport(Base):
    """A voluntary, self-reported pay figure. Never shown alone: only as a range for groups of at least ten."""
    __tablename__ = "salary_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    role_key: Mapped[str] = mapped_column(String(120), index=True)  # lower-cased role title
    role_title: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))  # full_time, internship_stipend
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    annual_amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "role_key", "city", "kind", name="uq_salary_one_per_user"),)


class FeedbackRequest(Base):
    __tablename__ = "feedback_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = _uid()
    token: Mapped[str] = mapped_column(String(64), unique=True)
    context: Mapped[str] = mapped_column(String(200))
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FeedbackNote(Base):
    __tablename__ = "feedback_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("feedback_requests.id", ondelete="CASCADE"), index=True)
    giver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    strengths: Mapped[str] = mapped_column(String(600))
    improve: Mapped[str] = mapped_column(String(600))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("request_id", "giver_id", name="uq_one_note_per_giver"),)

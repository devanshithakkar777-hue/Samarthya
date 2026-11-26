"""Personal progress: badges and a private activity streak.

Badges here are Samarthya internal recognition. They are not accredited qualifications and are always labelled so.
Nothing is ranked, compared between students, or awarded for time spent. Wellness activity is never counted.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m

INTERNAL_NOTE = "Samarthya internal badge. It shows your own progress and is not an accredited qualification."

# key: (title, description)
BADGES = {
    "profile-started": ("Profile started", "You saved your degree and interests."),
    "practice-10": ("Ten questions answered", "You answered 10 practice questions."),
    "practice-correct-50": ("Fifty correct answers", "You gave 50 correct answers in practice."),
    "assessment-first": ("First assessment", "You completed an assessment."),
    "assessment-80": ("Strong result", "You scored 80% or more on an assessment."),
    "scenario-first": ("First scenario", "You worked through a scenario to its end."),
    "scenario-5": ("Five scenarios", "You completed five scenarios."),
    "resume-first": ("First resume", "You built a resume from your master profile."),
    "evidence-builder": ("Evidence builder", "You attached evidence to three entries in your profile."),
    "defence-5": ("Ready to explain", "You practised defending five lines of your own resume."),
    "flashcards-50": ("Fifty reviews", "You reviewed flashcards 50 times."),
    "study-10": ("Ten tasks done", "You finished ten items in your study plan."),
    "applied-first": ("First application", "You tracked your first application."),
}


def touch(db: Session, user_id: int) -> list[str]:
    """Record that the student did something today, then award any badges now earned. Returns new badge keys."""
    today = date.today()
    row = db.get(m.ActivityDay, (user_id, today))
    if row is None:
        db.add(m.ActivityDay(user_id=user_id, day=today, count=1))
    else:
        row.count += 1
    db.flush()
    return award(db, user_id)


def _count(db: Session, stmt) -> int:
    return db.scalar(stmt) or 0


def earned_now(db: Session, uid: int) -> set[str]:
    out: set[str] = set()
    prof = db.get(m.Profile, uid)
    if prof and (prof.qualification_id or prof.interests):
        out.add("profile-started")
    answered = _count(db, select(func.count()).select_from(m.QuestionResponse).where(m.QuestionResponse.user_id == uid))
    right = _count(db, select(func.count()).select_from(m.QuestionResponse).where(
        m.QuestionResponse.user_id == uid, m.QuestionResponse.correct.is_(True)))
    if answered >= 10:
        out.add("practice-10")
    if right >= 50:
        out.add("practice-correct-50")
    done = db.scalars(select(m.AssessmentAttempt.score_pct).where(
        m.AssessmentAttempt.user_id == uid, m.AssessmentAttempt.submitted_at.is_not(None))).all()
    if done:
        out.add("assessment-first")
    if any((s or 0) >= 80 for s in done):
        out.add("assessment-80")
    runs = _count(db, select(func.count()).select_from(m.ScenarioRun).where(
        m.ScenarioRun.user_id == uid, m.ScenarioRun.completed.is_(True)))
    if runs >= 1:
        out.add("scenario-first")
    if runs >= 5:
        out.add("scenario-5")
    if _count(db, select(func.count()).select_from(m.Resume).where(m.Resume.user_id == uid)):
        out.add("resume-first")
    entries = db.scalars(select(m.MasterEntry.evidence).where(m.MasterEntry.user_id == uid)).all()
    if sum(1 for ev in entries if ev) >= 3:
        out.add("evidence-builder")
    if _count(db, select(func.count()).select_from(m.DefenceAnswer).where(m.DefenceAnswer.user_id == uid)) >= 5:
        out.add("defence-5")
    reps = _count(db, select(func.coalesce(func.sum(m.Flashcard.reps), 0)).join(
        m.FlashDeck, m.FlashDeck.id == m.Flashcard.deck_id).where(m.FlashDeck.user_id == uid))
    if reps >= 50:
        out.add("flashcards-50")
    if _count(db, select(func.count()).select_from(m.StudyItem).where(
            m.StudyItem.user_id == uid, m.StudyItem.status == "done")) >= 10:
        out.add("study-10")
    if _count(db, select(func.count()).select_from(m.Application).where(m.Application.user_id == uid)):
        out.add("applied-first")
    return out


def award(db: Session, uid: int) -> list[str]:
    have = set(db.scalars(select(m.UserBadge.badge_key).where(m.UserBadge.user_id == uid)))
    new = sorted(earned_now(db, uid) - have)
    for k in new:
        db.add(m.UserBadge(user_id=uid, badge_key=k))
    return new


def streak(db: Session, uid: int) -> dict:
    """Consecutive active days, forgiving one missed day. The number is private and only ever shown to its owner."""
    days = sorted(set(db.scalars(select(m.ActivityDay.day).where(m.ActivityDay.user_id == uid))), reverse=True)
    today, cur = date.today(), 0
    if not days:
        return {"current": 0, "active_days_last_30": 0}
    last = days[0]
    if (today - last).days <= 2:
        cur, prev = 1, last
        for d in days[1:]:
            if (prev - d).days <= 2:
                cur += 1
                prev = d
            else:
                break
    month = sum(1 for d in days if (today - d).days < 30)
    return {"current": cur, "active_days_last_30": month}

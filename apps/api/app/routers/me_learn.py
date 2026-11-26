"""Signed-in routes: study tools, practice, assessments, scenarios, progress, companion."""
import io
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import meta
from .. import models as m
from ..config import get_settings
from ..db import get_db
from ..deps import current_user
from ..services import ask, badges, engine, llm, practice, resume, srs
from ..services.safety import CRISIS_RESOURCES, crisis_signal
from ..services.scenario import public_node, step

router = APIRouter(prefix="/v1/me", tags=["me-learn"])
PUB = m.Status.published


def _own(db: Session, model, obj_id: int, user: m.User, field: str = "user_id"):
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, field) != user.id:
        raise HTTPException(404, "Not found")
    return obj


def _limit(db: Session, model, user: m.User, cap: int, what: str):
    if (db.scalar(select(func.count()).select_from(model).where(model.user_id == user.id)) or 0) >= cap:
        raise HTTPException(409, f"You have reached the limit of {cap} {what}. Delete some to add more.")


# ---------------------------------------------------------------- notes
class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=20000)
    folder: str | None = Field(default=None, max_length=80)
    ref_type: str | None = Field(default=None, pattern="^(lesson|library|role|skill|company)$")
    ref_id: int | None = None


def _note(n: m.UserNote) -> dict:
    return {"id": n.id, "title": n.title, "body": n.body, "folder": n.folder, "ref_type": n.ref_type, "ref_id": n.ref_id,
            "updated_at": n.updated_at.isoformat()}


@router.get("/notes")
def notes(folder: str | None = None, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(m.UserNote).where(m.UserNote.user_id == user.id)
    if folder:
        stmt = stmt.where(m.UserNote.folder == folder)
    return [_note(n) for n in db.scalars(stmt.order_by(m.UserNote.updated_at.desc()).limit(500))]


@router.post("/notes", status_code=201)
def add_note(body: NoteIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _limit(db, m.UserNote, user, 2000, "notes")
    n = m.UserNote(user_id=user.id, **body.model_dump())
    db.add(n)
    badges.touch(db, user.id)
    db.commit()
    return _note(n)


@router.put("/notes/{note_id}")
def edit_note(note_id: int, body: NoteIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    n = _own(db, m.UserNote, note_id, user)
    for k, v in body.model_dump().items():
        setattr(n, k, v)
    db.commit()
    return _note(n)


@router.delete("/notes/{note_id}", status_code=204)
def del_note(note_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.UserNote, note_id, user))
    db.commit()


# ---------------------------------------------------------------- flashcards
class DeckIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    subject: str | None = Field(default=None, max_length=120)


class CardIn(BaseModel):
    front: str = Field(min_length=1, max_length=2000)
    back: str = Field(min_length=1, max_length=2000)


class ReviewIn(BaseModel):
    rating: int


@router.get("/decks")
def decks(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    today = date.today()
    out = []
    for d in db.scalars(select(m.FlashDeck).where(m.FlashDeck.user_id == user.id).order_by(m.FlashDeck.title)):
        due = db.scalar(select(func.count()).select_from(m.Flashcard).where(m.Flashcard.deck_id == d.id, m.Flashcard.due <= today))
        total = db.scalar(select(func.count()).select_from(m.Flashcard).where(m.Flashcard.deck_id == d.id))
        out.append({"id": d.id, "title": d.title, "subject": d.subject, "cards": total, "due": due})
    return out


@router.post("/decks", status_code=201)
def add_deck(body: DeckIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _limit(db, m.FlashDeck, user, 200, "decks")
    d = m.FlashDeck(user_id=user.id, **body.model_dump())
    db.add(d)
    db.commit()
    return {"id": d.id, "title": d.title, "subject": d.subject, "cards": 0, "due": 0}


@router.delete("/decks/{deck_id}", status_code=204)
def del_deck(deck_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.FlashDeck, deck_id, user))
    db.commit()


@router.get("/decks/{deck_id}/cards")
def deck_cards(deck_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    d = _own(db, m.FlashDeck, deck_id, user)
    return [{"id": c.id, "front": c.front, "back": c.back, "due": c.due.isoformat(), "reps": c.reps}
            for c in db.scalars(select(m.Flashcard).where(m.Flashcard.deck_id == d.id).order_by(m.Flashcard.id))]


@router.post("/decks/{deck_id}/cards", status_code=201)
def add_card(deck_id: int, body: CardIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    d = _own(db, m.FlashDeck, deck_id, user)
    total = db.scalar(select(func.count()).select_from(m.Flashcard).join(m.FlashDeck).where(m.FlashDeck.user_id == user.id)) or 0
    if total >= 10000:
        raise HTTPException(409, "You have reached the limit of 10000 cards.")
    c = m.Flashcard(deck_id=d.id, front=body.front, back=body.back)
    db.add(c)
    db.commit()
    return {"id": c.id, "front": c.front, "back": c.back, "due": c.due.isoformat(), "reps": 0}


@router.delete("/cards/{card_id}", status_code=204)
def del_card(card_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(m.Flashcard, card_id)
    if c is None or c.deck.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(c)
    db.commit()


@router.get("/decks/{deck_id}/due")
def due_cards(deck_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    d = _own(db, m.FlashDeck, deck_id, user)
    rows = db.scalars(select(m.Flashcard).where(m.Flashcard.deck_id == d.id, m.Flashcard.due <= date.today())
                      .order_by(m.Flashcard.due, m.Flashcard.id).limit(30))
    return [{"id": c.id, "front": c.front, "back": c.back} for c in rows]


@router.post("/cards/{card_id}/review")
def review_card(card_id: int, body: ReviewIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(m.Flashcard, card_id)
    if c is None or c.deck.user_id != user.id:
        raise HTTPException(404, "Not found")
    try:
        srs.review(c, body.rating)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    new = badges.touch(db, user.id)
    db.commit()
    return {"next_due": c.due.isoformat(), "interval_days": c.interval_days, "new_badges": new}


# ---------------------------------------------------------------- study plan
class StudyIn(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=200)
    subject: str | None = Field(default=None, max_length=120)
    due_date: date | None = None
    status: str = Field(default="todo", pattern="^(todo|doing|done)$")
    notes: str | None = Field(default=None, max_length=4000)


def _study(s: m.StudyItem) -> dict:
    return {"id": s.id, "kind": s.kind, "title": s.title, "subject": s.subject, "due_date": s.due_date.isoformat() if s.due_date else None,
            "status": s.status, "notes": s.notes}


@router.get("/study")
def study(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.StudyItem).where(m.StudyItem.user_id == user.id).order_by(
        m.StudyItem.status == "done", m.StudyItem.due_date.asc().nullslast(), m.StudyItem.id).limit(500)).all()
    today = date.today()
    return {"items": [_study(r) for r in rows],
            "overdue": sum(1 for r in rows if r.status != "done" and r.due_date and r.due_date < today),
            "this_week": sum(1 for r in rows if r.status != "done" and r.due_date and today <= r.due_date <= today + timedelta(days=7)),
            "weak_topics": engine.weak_topics(db, user.id)}


def _check_kind(kind: str):
    if kind not in meta.STUDY_KINDS:
        raise HTTPException(422, "kind must be one of: " + ", ".join(sorted(meta.STUDY_KINDS)))


@router.post("/study", status_code=201)
def add_study(body: StudyIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _check_kind(body.kind)
    _limit(db, m.StudyItem, user, 2000, "study items")
    s = m.StudyItem(user_id=user.id, **body.model_dump())
    db.add(s)
    db.commit()
    return _study(s)


@router.put("/study/{item_id}")
def edit_study(item_id: int, body: StudyIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _check_kind(body.kind)
    s = _own(db, m.StudyItem, item_id, user)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    badges.touch(db, user.id)
    db.commit()
    return _study(s)


@router.delete("/study/{item_id}", status_code=204)
def del_study(item_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, m.StudyItem, item_id, user))
    db.commit()


# ---------------------------------------------------------------- adaptive practice (multiple choice)
class AnswerIn(BaseModel):
    question_id: int
    chosen: int = Field(ge=0, le=5)


@router.get("/practice/next")
def practice_next(pillar: str = Query(..., max_length=40), topic: str | None = Query(None, max_length=120),
                  user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    q = practice.pick_next(db, user.id, pillar, topic, "mcq")
    if q is None:
        return {"question": None, "message": "There are no published questions here yet."}
    tp = db.get(m.TopicProgress, (user.id, q.pillar, q.topic))
    return {"question": practice.public_question(q), "your_level": tp.level if tp else 1}


@router.post("/practice/answer")
def practice_answer(body: AnswerIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.get(m.Question, body.question_id)
    if q is None or q.status != PUB or q.kind != "mcq":
        raise HTTPException(404, "Not found")
    if body.chosen >= len(q.options):
        raise HTTPException(422, "That option does not exist")
    ok = body.chosen == q.correct_index
    db.add(m.QuestionResponse(user_id=user.id, question_id=q.id, chosen=body.chosen, correct=ok))
    tp = practice.record(db, user.id, q.pillar, q.topic, ok)
    new = badges.touch(db, user.id)
    db.commit()
    return {"correct": ok, "correct_index": q.correct_index, "explanation": q.explanation, "your_level": tp.level,
            "topic_accuracy": round(tp.correct / tp.attempts * 100), "new_badges": new}


@router.get("/practice/topics")
def practice_topics(pillar: str = Query(..., max_length=40), db: Session = Depends(get_db), user: m.User = Depends(current_user)):
    topics = {t: c for t, c in db.execute(select(m.Question.topic, func.count()).where(
        m.Question.status == PUB, m.Question.pillar == pillar, m.Question.kind == "mcq").group_by(m.Question.topic))}
    prog = {p.topic: p for p in db.scalars(select(m.TopicProgress).where(m.TopicProgress.user_id == user.id, m.TopicProgress.pillar == pillar))}
    return [{"topic": t, "questions": c, "level": prog[t].level if t in prog else 1,
             "accuracy": round(prog[t].correct / prog[t].attempts * 100) if t in prog and prog[t].attempts else None}
            for t, c in sorted(topics.items())]


# ---------------------------------------------------------------- open questions (interview and case prompts)
class OpenAnswerIn(BaseModel):
    question_id: int
    answer: str = Field(min_length=1, max_length=4000)
    ratings: dict[str, int] = Field(default_factory=dict)
    use_ai: bool = False


@router.get("/practice/open/next")
def open_next(pillar: str = Query("interview", max_length=40), role: str | None = Query(None, max_length=100),
              user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    stmt = select(m.Question).where(m.Question.status == PUB, m.Question.kind == "open", m.Question.pillar == pillar)
    if role:
        stmt = stmt.join(m.Role, m.Role.id == m.Question.role_id).where(m.Role.slug == role)
    pool = list(db.scalars(stmt))
    if not pool:
        return {"question": None, "message": "There are no published questions here yet."}
    seen = set(db.scalars(select(m.QuestionResponse.question_id).where(m.QuestionResponse.user_id == user.id)
                          .order_by(m.QuestionResponse.id.desc()).limit(15)))
    import random
    q = random.choice([x for x in pool if x.id not in seen] or pool)
    return {"question": practice.public_question(q)}


@router.post("/practice/open/answer")
def open_answer(body: OpenAnswerIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.get(m.Question, body.question_id)
    if q is None or q.status != PUB or q.kind != "open":
        raise HTTPException(404, "Not found")
    ratings = {k: v for k, v in body.ratings.items() if k in ("clarity", "depth", "relevance", "confidence") and 1 <= v <= 5}
    feedback = resume.answer_feedback(body.answer)
    ai, ai_note = None, None
    if body.use_ai:
        if llm.enabled() and _ai_allowed(user.id):
            try:
                ai = llm.evaluate(q.stem, q.guidance or "", body.answer)
            except llm.LlmUnavailable as e:
                ai_note = str(e)
        else:
            ai_note = "AI feedback is not switched on."
    db.add(m.QuestionResponse(user_id=user.id, question_id=q.id, answer_text=body.answer, ratings=ratings or None))
    new = badges.touch(db, user.id)
    db.commit()
    return {"guidance": q.guidance, "automatic_checks": feedback, "ai_feedback": ai, "ai_note": ai_note, "new_badges": new,
            "note": "Automatic checks look at structure only. Compare your answer with the guidance and be honest with yourself."}


# ---------------------------------------------------------------- assessments
class SubmitIn(BaseModel):
    answers: dict[str, int] = Field(default_factory=dict)


def _assessment_questions(db: Session, a: m.Assessment) -> list[m.Question]:
    by = {q.slug: q for q in db.scalars(select(m.Question).where(m.Question.slug.in_(a.question_slugs or []), m.Question.status == PUB))}
    return [by[s] for s in a.question_slugs if s in by]


@router.post("/assessments/{slug}/start", status_code=201)
def start_assessment(slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    a = db.scalar(select(m.Assessment).where(m.Assessment.slug == slug, m.Assessment.status == PUB))
    if a is None:
        raise HTTPException(404, "Not found")
    qs = _assessment_questions(db, a)
    if len(qs) < 3:
        raise HTTPException(409, "This assessment is not ready yet")
    att = m.AssessmentAttempt(user_id=user.id, assessment_id=a.id)
    db.add(att)
    db.commit()
    return {"attempt_id": att.id, "title": a.title, "duration_minutes": a.duration_minutes,
            "questions": [practice.public_question(q) for q in qs]}


@router.post("/assessments/attempts/{attempt_id}/submit")
def submit_assessment(attempt_id: int, body: SubmitIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    att = _own(db, m.AssessmentAttempt, attempt_id, user)
    if att.submitted_at is not None:
        raise HTTPException(409, "This attempt was already submitted")
    a = att.assessment
    qs = _assessment_questions(db, a)
    now = datetime.now(timezone.utc)
    review, right, per = [], 0, {}
    for q in qs:
        chosen = body.answers.get(str(q.id))
        ok = chosen is not None and chosen == q.correct_index
        right += ok
        t = per.setdefault(q.topic, {"correct": 0, "total": 0})
        t["total"] += 1
        t["correct"] += ok
        review.append({"question_id": q.id, "stem": q.stem, "options": q.options, "chosen": chosen, "correct_index": q.correct_index,
                       "correct": ok, "explanation": q.explanation})
        db.add(m.QuestionResponse(user_id=user.id, question_id=q.id, chosen=chosen, correct=ok))
    score = round(right / len(qs) * 100, 1) if qs else 0.0
    att.answers, att.score_pct, att.per_topic, att.submitted_at = body.answers, score, per, now
    overtime = bool(a.duration_minutes and (now - att.started_at).total_seconds() > a.duration_minutes * 60 + 30)
    new = badges.touch(db, user.id)
    db.commit()
    cred = {"internal": badges.INTERNAL_NOTE, "partner": f"This is a partner credential issued by {a.issuer}. Samarthya only records your internal result here.",
            "accredited": f"Any accredited credential is issued by {a.issuer}, not by Samarthya. This page records your internal result."}[a.credential_type]
    return {"score_pct": score, "correct": right, "total": len(qs), "by_topic": per, "review": review, "over_time_limit": overtime,
            "credential_statement": cred, "new_badges": new}


@router.get("/assessments/attempts")
def attempts(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.AssessmentAttempt).where(m.AssessmentAttempt.user_id == user.id,
                                                        m.AssessmentAttempt.submitted_at.is_not(None))
                      .order_by(m.AssessmentAttempt.submitted_at.desc()).limit(200))
    return [{"id": r.id, "assessment": r.assessment.title, "slug": r.assessment.slug, "score_pct": r.score_pct,
             "date": r.submitted_at.date().isoformat(), "credential_type": r.assessment.credential_type, "by_topic": r.per_topic}
            for r in rows]


@router.get("/transcript.pdf")
def transcript_pdf(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    st = getSampleStyleSheet()
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, title="Samarthya learning transcript")
    flow = [Paragraph("Samarthya learning transcript", st["Title"]),
            Paragraph("An internal record of your own practice and assessments on Samarthya. It is not an accredited "
                      "qualification and is not issued by any university or examining body.", st["Normal"]), Spacer(1, 12)]
    rows = attempts(user, db)
    flow.append(Paragraph("Assessments", st["Heading2"]))
    for r in rows or []:
        flow.append(Paragraph(f"{r['date']} - {r['assessment']}: {r['score_pct']}%", st["Normal"]))
    if not rows:
        flow.append(Paragraph("No assessments completed yet.", st["Normal"]))
    flow.append(Paragraph("Badges", st["Heading2"]))
    keys = list(db.scalars(select(m.UserBadge.badge_key).where(m.UserBadge.user_id == user.id)))
    for k in keys:
        if k in badges.BADGES:
            flow.append(Paragraph(f"{badges.BADGES[k][0]} - {badges.BADGES[k][1]}", st["Normal"]))
    if not keys:
        flow.append(Paragraph("No badges yet.", st["Normal"]))
    pdf.build(flow)
    return Response(buf.getvalue(), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="samarthya-transcript.pdf"'})


# ---------------------------------------------------------------- scenarios
class ChooseIn(BaseModel):
    choice: int = Field(ge=0, le=9)


@router.post("/scenarios/{slug}/start", status_code=201)
def start_scenario(slug: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.scalar(select(m.Scenario).where(m.Scenario.slug == slug, m.Scenario.status == PUB))
    if s is None:
        raise HTTPException(404, "Not found")
    run = m.ScenarioRun(user_id=user.id, scenario_id=s.id, current=s.nodes[0]["key"], scores={d: 0 for d in s.dimensions}, path=[])
    db.add(run)
    db.commit()
    return {"run_id": run.id, "title": s.title, "brief": s.brief, "dimensions": s.dimensions, "scene": public_node(s.nodes[0])}


@router.post("/scenarios/runs/{run_id}/choose")
def choose(run_id: int, body: ChooseIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    run = _own(db, m.ScenarioRun, run_id, user)
    if run.completed:
        raise HTTPException(409, "This run is finished")
    s = run.scenario
    try:
        c, deltas, nxt = step(s.nodes, run.current, body.choice)
    except (ValueError, KeyError) as e:
        raise HTTPException(422, "That choice is not available") from e
    scores = dict(run.scores)
    for d, v in deltas.items():
        scores[d] = scores.get(d, 0) + v
    run.scores, run.path = scores, list(run.path) + [{"scene": run.current, "choice": body.choice, "label": c["label"]}]
    run.current = nxt["key"]
    out = {"consequence": c["consequence"], "scene": public_node(nxt), "scores": scores}
    if nxt.get("end"):
        run.completed = True
        out["finished"] = True
        out["summary"] = {"dimensions": scores, "path": run.path,
                          "note": "Scores show how your choices leaned on each dimension. There is rarely one correct path; read the debrief."}
        out["new_badges"] = badges.touch(db, user.id)
    db.commit()
    return out


@router.get("/scenarios/runs")
def runs(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.ScenarioRun).where(m.ScenarioRun.user_id == user.id, m.ScenarioRun.completed.is_(True))
                      .order_by(m.ScenarioRun.id.desc()).limit(100))
    return [{"id": r.id, "title": r.scenario.title, "slug": r.scenario.slug, "scores": r.scores, "date": r.created_at.date().isoformat()}
            for r in rows]


# ---------------------------------------------------------------- progress, recommendations
@router.get("/progress")
def progress(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    earned = {b.badge_key: b.awarded_at for b in db.scalars(select(m.UserBadge).where(m.UserBadge.user_id == user.id))}
    topics = [{"pillar": t.pillar, "topic": t.topic, "level": t.level, "attempts": t.attempts,
               "accuracy": round(t.correct / t.attempts * 100) if t.attempts else None}
              for t in db.scalars(select(m.TopicProgress).where(m.TopicProgress.user_id == user.id).order_by(m.TopicProgress.pillar, m.TopicProgress.topic))]

    def n(model, *w):
        return db.scalar(select(func.count()).select_from(model).where(model.user_id == user.id, *w)) or 0

    return {"badges": [{"key": k, "title": badges.BADGES[k][0], "description": badges.BADGES[k][1], "earned": k in earned,
                        "awarded_on": earned[k].date().isoformat() if k in earned else None} for k in badges.BADGES],
            "badge_note": badges.INTERNAL_NOTE, "streak": badges.streak(db, user.id), "topics": topics,
            "counts": {"questions_answered": n(m.QuestionResponse), "assessments": n(m.AssessmentAttempt, m.AssessmentAttempt.submitted_at.is_not(None)),
                       "scenarios": n(m.ScenarioRun, m.ScenarioRun.completed.is_(True)), "resumes": n(m.Resume),
                       "study_done": n(m.StudyItem, m.StudyItem.status == "done")},
            "principle": "This is your own progress. It is never ranked against other students. It is shared only if you create a parent link yourself, and you can cancel that link at any time."}


@router.get("/recommendations")
def recommendations(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return engine.recommend(db, user.id)


# ---------------------------------------------------------------- companion
_USAGE: dict[tuple[int, date], int] = {}


def _ai_allowed(uid: int) -> bool:
    key = (uid, date.today())
    for k in [k for k in _USAGE if k[1] != date.today()]:
        _USAGE.pop(k, None)
    if _USAGE.get(key, 0) >= get_settings().llm_daily_limit:
        return False
    _USAGE[key] = _USAGE.get(key, 0) + 1
    return True


class CompanionIn(BaseModel):
    question: str = Field(min_length=2, max_length=1500)


@router.get("/companion/status")
def companion_status(_: m.User = Depends(current_user)):
    return {"ai_enabled": llm.enabled(), "daily_limit": get_settings().llm_daily_limit}


@router.post("/companion")
def companion(body: CompanionIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    q = " ".join(body.question.split())
    if crisis_signal(q):
        return {"mode": "safety", "answer": "I'm really sorry you're feeling this way. You do not have to handle it alone. "
                "Please talk to someone now: the free helplines below are open and confidential, and if you are in immediate danger call 112. "
                "If there is a person you trust nearby, tell them how you are feeling.", "citations": [], "crisis_resources": CRISIS_RESOURCES}
    passages = ask.top_passages(db, q)
    if llm.enabled():
        if not _ai_allowed(user.id):
            raise HTTPException(429, "You have reached today's limit for the companion. The rest of Samarthya is still here for you.")
        try:
            res = llm.chat(q, passages)
            return {"mode": "ai", **res, "note": "AI-written. Facts are cited to Samarthya's sourced pages; anything marked Suggestion is not sourced. Check important details on the official page."}
        except llm.LlmUnavailable:
            pass
    res = ask.answer(db, q)
    return {"mode": "retrieval", "answer": res["answer"], "citations": res["citations"],
            "note": "The AI companion is not switched on. This answer is copied from sourced pages." if not llm.enabled() else
                    "The AI companion is unavailable right now, so this answer is copied from sourced pages."}

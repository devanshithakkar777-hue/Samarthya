"""Adaptive practice: difficulty follows the student's recent results in each topic."""
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m


def adjust_level(level: int, recent: list[int]) -> int:
    last3 = recent[-3:]
    if len(last3) == 3 and sum(last3) == 3 and level < 3:
        return level + 1
    if len(last3) >= 2 and last3.count(0) >= 2 and level > 1:
        return level - 1
    return level


def record(db: Session, user_id: int, pillar: str, topic: str, correct: bool) -> m.TopicProgress:
    tp = db.get(m.TopicProgress, (user_id, pillar, topic))
    if tp is None:
        tp = m.TopicProgress(user_id=user_id, pillar=pillar, topic=topic, level=1, attempts=0, correct=0, recent=[])
        db.add(tp)
    tp.attempts += 1
    tp.correct += 1 if correct else 0
    tp.recent = (list(tp.recent or []) + [1 if correct else 0])[-8:]
    tp.level = adjust_level(tp.level, tp.recent)
    return tp


def pick_next(db: Session, user_id: int, pillar: str, topic: str | None, kind: str = "mcq") -> m.Question | None:
    level = 1
    if topic:
        tp = db.get(m.TopicProgress, (user_id, pillar, topic))
        level = tp.level if tp else 1
    q = select(m.Question).where(m.Question.status == m.Status.published, m.Question.pillar == pillar,
                                 m.Question.kind == kind)
    if topic:
        q = q.where(m.Question.topic == topic)
    pool = list(db.scalars(q))
    if not pool:
        return None
    seen_recent = set(db.scalars(select(m.QuestionResponse.question_id).where(
        m.QuestionResponse.user_id == user_id).order_by(m.QuestionResponse.id.desc()).limit(25)))
    fresh = [x for x in pool if x.id not in seen_recent] or pool
    at_level = [x for x in fresh if x.difficulty == level] or sorted(fresh, key=lambda x: abs(x.difficulty - level))
    # prefer the closest difficulty, then a random one among equals so a topic does not repeat in a fixed order
    best = min(abs(x.difficulty - level) for x in at_level)
    return random.choice([x for x in at_level if abs(x.difficulty - level) == best])


def public_question(q: m.Question) -> dict:
    """The question without its answer."""
    return {"id": q.id, "slug": q.slug, "pillar": q.pillar, "topic": q.topic, "kind": q.kind, "stem": q.stem,
            "options": q.options if q.kind == "mcq" else [], "difficulty": q.difficulty}

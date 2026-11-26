"""Personalised learning engine. Rule-based and explainable: every recommendation says why it is shown.

Starts from what the student has told us (degree, year, interests, skills they report, roles they saved) and what
they have done (assessments, practice). Finds skills the saved roles ask for that the student has not shown yet,
then lines up published lessons, library items, resources, scenarios and opportunities that address them.
"""
from urllib.parse import quote
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models as m

PUB = m.Status.published


def _targets(db: Session, uid: int) -> list[m.Role]:
    ids = list(db.scalars(select(m.SavedItem.entity_id).where(m.SavedItem.user_id == uid, m.SavedItem.entity_type == "role")))
    if not ids:
        return []
    return list(db.scalars(select(m.Role).where(m.Role.id.in_(ids), m.Role.status == PUB).options(
        selectinload(m.Role.requirements))))


def skill_gaps(db: Session, uid: int) -> list[dict]:
    prof = db.get(m.Profile, uid)
    have = set(prof.skills) if prof else set()
    out: dict[int, dict] = {}
    for role in _targets(db, uid):
        for req in role.requirements:
            if req.skill_id is None:
                continue
            sk = db.get(m.Skill, req.skill_id)
            if sk is None or sk.status != PUB or sk.slug in have:
                continue
            g = out.setdefault(sk.id, {"skill_id": sk.id, "slug": sk.slug, "name": sk.name, "needed_for": [], "tiers": set()})
            g["needed_for"].append(role.title)
            g["tiers"].add(req.tier.value)
    order = {"mandatory": 0, "common_preference": 1, "recommended": 2, "differentiator": 3}
    gaps = []
    for g in out.values():
        g["tiers"] = sorted(g["tiers"], key=lambda t: order[t])
        g["priority"] = order[g["tiers"][0]]
        gaps.append(g)
    return sorted(gaps, key=lambda g: (g["priority"], -len(g["needed_for"]), g["name"]))


def weak_topics(db: Session, uid: int) -> list[dict]:
    rows = db.scalars(select(m.TopicProgress).where(m.TopicProgress.user_id == uid, m.TopicProgress.attempts >= 3))
    weak = [{"pillar": r.pillar, "topic": r.topic, "accuracy": round(r.correct / r.attempts * 100), "attempts": r.attempts}
            for r in rows if r.correct / r.attempts < 0.6]
    return sorted(weak, key=lambda w: w["accuracy"])


def recommend(db: Session, uid: int) -> dict:
    prof = db.get(m.Profile, uid)
    gaps = skill_gaps(db, uid)[:6]
    recs: list[dict] = []
    for g in gaps:
        why = f"Needed for {', '.join(g['needed_for'][:2])} ({g['tiers'][0].replace('_', ' ')})"
        for res in db.scalars(select(m.LearningResource).where(m.LearningResource.skill_id == g["skill_id"],
                                                               m.LearningResource.status == PUB).order_by(
                m.LearningResource.price_inr).limit(2)):
            recs.append({"kind": "resource", "title": res.title, "path": f"/skills/{g['slug']}", "why": why,
                         "detail": f"{res.provider}, {'free' if res.price_inr == 0 else '₹' + str(res.price_inr)}"})
        for les in db.scalars(select(m.Lesson).where(m.Lesson.skill_id == g["skill_id"], m.Lesson.status == PUB).limit(2)):
            recs.append({"kind": "lesson", "title": les.title, "path": f"/academy/{les.slug}", "why": why, "detail": les.track})
    for w in weak_topics(db, uid)[:3]:
        for les in db.scalars(select(m.Lesson).where(m.Lesson.pillar == w["pillar"], m.Lesson.track == w["topic"],
                                                     m.Lesson.status == PUB).limit(1)):
            recs.append({"kind": "lesson", "title": les.title, "path": f"/academy/{les.slug}",
                         "why": f"Your recent accuracy in {w['topic']} is {w['accuracy']}%", "detail": les.track})
        recs.append({"kind": "practice", "title": f"Practise {w['topic']}", "path": f"/practise/drill?pillar={quote(w['pillar'])}&topic={quote(w['topic'])}",
                     "why": f"Your recent accuracy in {w['topic']} is {w['accuracy']}% over {w['attempts']} answers", "detail": w["pillar"]})
    sector_ids = {r.sector_id for r in _targets(db, uid)}
    if sector_ids:
        for sc in db.scalars(select(m.Scenario).where(m.Scenario.sector_id.in_(sector_ids), m.Scenario.status == PUB).limit(3)):
            recs.append({"kind": "scenario", "title": sc.title, "path": f"/practise/cases/{sc.slug}",
                         "why": "A case in a sector you saved", "detail": sc.pillar})
    year = prof.year_of_study if prof else None
    opp_q = select(m.Opportunity).where(m.Opportunity.status == PUB, (m.Opportunity.rolling.is_(True)) | (
        m.Opportunity.deadline >= date.today())).order_by(m.Opportunity.deadline.asc().nullslast()).limit(30)
    gap_slugs = {g["slug"] for g in gaps}
    for opp in db.scalars(opp_q):
        if year and ((opp.min_year and year < opp.min_year) or (opp.max_year and year > opp.max_year)):
            continue
        matched = gap_slugs & set(opp.skills or [])
        if matched or sector_ids & {opp.sector_id}:
            recs.append({"kind": "opportunity", "title": opp.title, "path": f"/opportunities/{opp.slug}",
                         "why": "Matches a skill you are building" if matched else "In a sector you saved",
                         "detail": opp.organisation})
    return {"skill_gaps": [{k: v for k, v in g.items() if k != "skill_id"} for g in gaps], "recommendations": recs[:20],
            "basis": "Based only on the roles you saved, the skills you reported, and your practice results. Nothing is predicted about your future."}

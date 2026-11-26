"""Public content, publish checks, practice, spaced repetition, assessments, scenarios, calculators, safety."""
from datetime import date, timedelta

import pytest

from app import models as m
from app.services import scenario, srs
from app.services.practice import adjust_level
from app.services.safety import contains_contact_details, crisis_signal
from .factories import make_source, make_user, published, session


def seed_questions(n=4, pillar="foundations", topic="t1"):
    with session() as db:
        src = make_source(db, "https://example.org/q")
        qs = [published(db, m.Question, src, slug=f"q-{i}", pillar=pillar, topic=topic, kind="mcq", stem=f"Fake question {i}?",
                        options=["a", "b", "c"], correct_index=1, explanation="Because b.", difficulty=1) for i in range(n)]
        db.commit()
        return [q.slug for q in qs]


# ------------------------------------------------------------ editorial publish checks
def _submit(client, ed, entity, payload):
    r = client.post(f"/v1/admin/{entity}", headers=ed, json=payload)
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    return rid, client.post(f"/v1/admin/{entity}/{rid}/submit", headers=ed)


def test_lesson_needs_substantial_body_and_source(client):
    _, ed = make_user("ed@example.org", m.UserRole.editor)
    with session() as db:
        src = make_source(db).id
        db.commit()
    base = {"slug": "l1", "pillar": "foundations", "track": "x", "title": "T", "summary": "S", "body": "too short",
            "source_id": src, "last_verified": date.today().isoformat()}
    _, r = _submit(client, ed, "lessons", base)
    assert r.status_code == 409
    ok = {**base, "slug": "l2", "body": "A real lesson body. " * 10}
    _, r = _submit(client, ed, "lessons", ok)
    assert r.json()["status"] == "in_review"


def test_unknown_choice_value_is_rejected(client):
    _, ed = make_user("ed@example.org", m.UserRole.editor)
    r = client.post("/v1/admin/lessons", headers=ed, json={"slug": "l9", "pillar": "not-a-pillar", "track": "x", "title": "T", "summary": "S", "body": "b"})
    assert r.status_code == 422


def test_library_item_must_state_its_licence_basis(client):
    _, ed = make_user("ed@example.org", m.UserRole.editor)
    with session() as db:
        src = make_source(db).id
        db.commit()
    base = {"slug": "b1", "title": "Book", "kind": "book", "subject": "s", "access_url": "http://insecure.example.org/b",
            "licence_status": "open_access", "source_id": src, "last_verified": date.today().isoformat()}
    _, r = _submit(client, ed, "library_items", base)
    assert r.status_code == 409  # http link and no licence note
    _, r = _submit(client, ed, "library_items", {**base, "slug": "b2", "access_url": "https://example.org/b", "licence_note": "CC BY, see page"})
    assert r.json()["status"] == "in_review"


def test_scenario_graph_is_validated_on_submit(client):
    _, ed = make_user("ed@example.org", m.UserRole.editor)
    with session() as db:
        src = make_source(db).id
        db.commit()
    bad = {"slug": "s1", "title": "S", "pillar": "case", "brief": "b", "dimensions": ["ethics"], "difficulty": 1, "minutes": 5,
           "nodes": [{"key": "a", "text": "t", "choices": [{"label": "x", "consequence": "c", "next": "zzz", "scores": {}}]}],
           "source_id": src, "last_verified": date.today().isoformat()}
    _, r = _submit(client, ed, "scenarios", bad)
    assert r.status_code == 409


# ------------------------------------------------------------ scenario engine
def graph():
    return [
        {"key": "start", "text": "Begin", "choices": [
            {"label": "Honest", "next": "good", "consequence": "ok", "scores": {"ethics": 2}},
            {"label": "Shortcut", "next": "bad", "consequence": "hmm", "scores": {"ethics": -2}}]},
        {"key": "good", "text": "Good", "end": True, "debrief": "Well done"},
        {"key": "bad", "text": "Bad", "end": True, "debrief": "Reflect"}]


def test_scenario_validation_rules():
    assert scenario.validate(graph(), ["ethics"]) == []
    loop = graph()
    loop[1] = {"key": "good", "text": "g", "choices": [{"label": "a", "next": "start", "consequence": "c", "scores": {}},
                                                       {"label": "b", "next": "bad", "consequence": "c", "scores": {}}]}
    assert any("loop" in e or "cycle" in e for e in scenario.validate(loop, ["ethics"]))
    assert scenario.validate(graph(), []) != []
    unreachable = graph() + [{"key": "orphan", "text": "o", "end": True, "debrief": "d"}]
    assert scenario.validate(unreachable, ["ethics"]) != []
    big = graph()
    big[0]["choices"][0]["scores"] = {"ethics": 9}
    assert scenario.validate(big, ["ethics"]) != []


def test_scenario_play_through_api(client):
    _, st = make_user("s@example.org")
    with session() as db:
        src = make_source(db)
        published(db, m.Scenario, src, slug="sc", title="Sc", pillar="case", brief="b", dimensions=["ethics"], nodes=graph(), difficulty=1, minutes=5)
        db.commit()
    assert "nodes" not in client.get("/v1/scenarios/sc").text or "debrief" not in client.get("/v1/scenarios/sc").text  # only the first scene is public
    run = client.post("/v1/me/scenarios/sc/start", headers=st).json()
    r = client.post(f"/v1/me/scenarios/runs/{run['run_id']}/choose", headers=st, json={"choice": 0}).json()
    assert r["finished"] is True and "Well done" in str(r)
    again = client.post(f"/v1/me/scenarios/runs/{run['run_id']}/choose", headers=st, json={"choice": 0})
    assert again.status_code in (409, 422)
    _, other = make_user("o@example.org")
    assert client.post(f"/v1/me/scenarios/runs/{run['run_id']}/choose", headers=other, json={"choice": 0}).status_code == 404


# ------------------------------------------------------------ spaced repetition
class Card:
    def __init__(self):
        self.reps, self.interval_days, self.ease, self.lapses, self.due = 0, 0, 2.5, 0, date.today()


def test_srs_intervals_grow_and_lapse_resets():
    c = Card()
    srs.review(c, 4)
    assert c.interval_days == 1
    srs.review(c, 4)
    assert c.interval_days == 6
    srs.review(c, 5)
    assert c.interval_days > 6
    big = c.interval_days
    srs.review(c, 1)
    assert c.interval_days == 1 and c.lapses == 1 and big > 6
    assert c.ease >= 1.3
    with pytest.raises(ValueError):
        srs.review(c, 2)


def test_flashcards_through_api_are_private(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    deck = client.post("/v1/me/decks", headers=a, json={"title": "D"}).json()
    card = client.post(f"/v1/me/decks/{deck['id']}/cards", headers=a, json={"front": "f", "back": "b"}).json()
    assert len(client.get(f"/v1/me/decks/{deck['id']}/due", headers=a).json()) == 1
    r = client.post(f"/v1/me/cards/{card['id']}/review", headers=a, json={"rating": 4})
    assert r.status_code == 200
    assert client.get(f"/v1/me/decks/{deck['id']}/due", headers=a).json() == []
    assert client.get(f"/v1/me/decks/{deck['id']}/due", headers=b).status_code == 404
    assert client.post(f"/v1/me/cards/{card['id']}/review", headers=b, json={"rating": 4}).status_code == 404
    assert client.post(f"/v1/me/cards/{card['id']}/review", headers=a, json={"rating": 2}).status_code == 422


# ------------------------------------------------------------ practice
def test_adaptive_level_moves_with_results():
    assert adjust_level(1, [1, 1, 1, 1]) == 2
    assert adjust_level(2, [0, 0, 0, 0]) == 1
    assert adjust_level(1, [0, 0, 0, 0]) == 1
    assert adjust_level(3, [1, 1, 1, 1, 1]) == 3


def test_practice_does_not_leak_the_answer_and_records_progress(client):
    seed_questions()
    _, st = make_user("s@example.org")
    q = client.get("/v1/me/practice/next", headers=st, params={"pillar": "foundations", "topic": "t1"}).json()["question"]
    assert "correct_index" not in q and "explanation" not in q
    r = client.post("/v1/me/practice/answer", headers=st, json={"question_id": q["id"], "chosen": 1}).json()
    assert r["correct"] is True and r["explanation"]
    r2 = client.post("/v1/me/practice/answer", headers=st, json={"question_id": q["id"], "chosen": 0}).json()
    assert r2["correct"] is False
    prog = client.get("/v1/me/progress", headers=st).json()
    assert prog["counts"] or prog["topics"]
    assert client.get("/v1/me/practice/next", headers=st, params={"pillar": "foundations", "topic": "nope"}).status_code in (200, 404)


def test_unpublished_questions_are_never_served(client):
    with session() as db:
        src = make_source(db)
        db.add(m.Question(slug="d", pillar="foundations", topic="t1", kind="mcq", stem="draft", options=["a", "b"], correct_index=0,
                          explanation="x", difficulty=1, status=m.Status.draft, source_id=src.id))
        db.commit()
        qid = db.query(m.Question).one().id
    _, st = make_user("s@example.org")
    assert client.get("/v1/me/practice/next", headers=st, params={"pillar": "foundations", "topic": "t1"}).status_code in (200, 404)
    assert client.post("/v1/me/practice/answer", headers=st, json={"question_id": qid, "chosen": 0}).status_code == 404


# ------------------------------------------------------------ assessments
def test_assessment_attempt_scores_and_is_labelled_internal(client):
    slugs = seed_questions(4, topic="a")
    with session() as db:
        src = make_source(db, "https://example.org/a")
        published(db, m.Assessment, src, slug="as1", title="Check", pillar="foundations", description="d", duration_minutes=10,
                  question_slugs=slugs, credential_type="internal")
        db.commit()
    _, st = make_user("s@example.org")
    start = client.post("/v1/me/assessments/as1/start", headers=st).json()
    assert all("correct_index" not in q for q in start["questions"])
    answers = {str(q["id"]): 1 for q in start["questions"]}
    done = client.post(f"/v1/me/assessments/attempts/{start['attempt_id']}/submit", headers=st, json={"answers": answers}).json()
    assert done["correct"] == done["total"] == 4 and done["score_pct"] == 100
    assert "internal" in done["credential_statement"].lower() or "not" in done["credential_statement"].lower()
    assert client.post(f"/v1/me/assessments/attempts/{start['attempt_id']}/submit", headers=st, json={"answers": answers}).status_code == 409
    _, other = make_user("o@example.org")
    assert client.post(f"/v1/me/assessments/attempts/{start['attempt_id']}/submit", headers=other, json={"answers": {}}).status_code == 404
    pdf = client.get("/v1/me/transcript.pdf", headers=st)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


# ------------------------------------------------------------ calculators
def test_calculators_state_assumptions_and_reject_bad_input(client):
    r = client.post("/v1/calc/emi", json={"principal": 100000, "annual_rate_pct": 10, "months": 12}).json()
    assert 8780 < r["monthly_payment"] < 8800 and r["assumptions"]
    assert client.post("/v1/calc/emi", json={"principal": -1, "annual_rate_pct": 10, "months": 12}).status_code == 422
    g = client.post("/v1/calc/growth", json={"principal": 1000, "annual_rate_pct": 0, "years": 5}).json()
    assert round(g["final_value"]) == 1000
    assert client.post("/v1/calc/nothing", json={}).status_code == 404
    b = client.post("/v1/calc/budget", json={"monthly_income": 10000}).json()
    assert round(b["needs"] + b["wants"] + b["savings_and_debt"]) == 10000


# ------------------------------------------------------------ safety
def test_crisis_and_contact_detection():
    assert crisis_signal("I want to end my life")
    assert not crisis_signal("I want to end my exam stress with a walk")
    assert contains_contact_details("call me on 98765 43210")
    assert contains_contact_details("mail me at a@b.com")
    assert contains_contact_details("whatsapp me")
    assert not contains_contact_details("I scored 98 in 2024 and joined a 12-week course")


def test_crisis_resources_are_public_and_sourced(client):
    r = client.get("/v1/crisis").json()
    items = r["resources"] if isinstance(r, dict) else r
    assert items and all(i.get("source") for i in items)
    assert "no-store" not in client.get("/v1/crisis").headers.get("cache-control", "")


# ------------------------------------------------------------ opportunities
def test_expired_opportunities_are_hidden_and_drafts_never_shown(client):
    with session() as db:
        src = make_source(db)
        mk = lambda slug, dl: published(db, m.Opportunity, src, slug=slug, title=slug, organisation="Org", kind="internship",
                                        description="d", eligibility="e", apply_url="https://example.org/apply", deadline=dl)
        mk("open", date.today() + timedelta(days=5))
        mk("gone", date.today() - timedelta(days=1))
        mk("rolling", None).rolling = True
        db.add(m.Opportunity(slug="draft", title="draft", organisation="O", kind="internship", description="d", eligibility="e",
                             apply_url="https://example.org/x", status=m.Status.draft))
        db.commit()
    slugs = {o["slug"] for o in client.get("/v1/opportunities").json()["results"]}
    assert slugs == {"open", "rolling"}
    assert client.get("/v1/opportunities/gone").json()["expired"] is True  # a shared link still opens, clearly marked closed
    assert client.get("/v1/opportunities/draft").status_code == 404


def test_skills_list_is_public_and_published_only(client):
    with session() as db:
        src = make_source(db)
        published(db, m.Skill, src, slug="sk-a", name="Alpha", category="Tech", overview="o")
        db.add(m.Skill(slug="sk-d", name="Draft", category="Tech", overview="o", status=m.Status.draft))
        db.commit()
    got = client.get("/v1/skills").json()["results"]
    assert [x["slug"] for x in got] == ["sk-a"]
    assert [x["slug"] for x in client.get("/v1/skills", params={"q": "tech"}).json()["results"]] == ["sk-a"]

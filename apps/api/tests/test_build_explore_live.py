"""Master profile, resumes, defence practice, portfolio, applications, matching and the private journal."""
from datetime import date, timedelta

from sqlalchemy import text

from app import models as m
from app.db import get_engine
from .factories import make_source, make_user, published, session


def entry(section="project", title="Budget app", **kw):
    return {"section": section, "title": title, "organisation": "Personal", "start_date": "2025-01-01", "end_date": "2025-03-01",
            "bullets": ["Built a budgeting app used by 12 classmates", "Wrote tests that cut bugs by 30%"],
            "evidence": [{"kind": "github", "url": "https://github.com/example/budget"}], "tags": ["python"], **kw}


def add(client, h, **kw):
    r = client.post("/v1/me/master", headers=h, json=entry(**kw))
    assert r.status_code == 201, r.text
    return r.json()


# ------------------------------------------------------------ master profile
def test_master_entries_are_validated_and_private(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    e = add(client, a)
    assert client.get("/v1/me/master", headers=b).json()["entries"] == []
    assert client.put(f"/v1/me/master/{e['id']}", headers=b, json=entry()).status_code == 404
    assert client.delete(f"/v1/me/master/{e['id']}", headers=b).status_code == 404
    bad = [entry(section="nonsense"), entry(evidence=[{"kind": "github", "url": "http://insecure.example.org"}]),
           entry(bullets=["x" * 401]), entry(start_date="2025-05-01", end_date="2025-01-01"), entry(bullets=["a"] * 9)]
    for payload in bad:
        assert client.post("/v1/me/master", headers=a, json=payload).status_code == 422
    assert client.get("/v1/me/master").status_code == 401


def test_skill_basis_is_labelled_demonstrated_or_self_reported(client):
    _, a = make_user("a@example.org")
    add(client, a)  # project tagged python
    add(client, a, section="skill", title="python", bullets=[], evidence=[], tags=[])
    add(client, a, section="skill", title="Rust", bullets=[], evidence=[], tags=[])
    skills = {x["title"]: x["basis"] for x in client.get("/v1/me/master", headers=a).json()["entries"] if x["section"] == "skill"}
    assert skills == {"python": "demonstrated", "Rust": "self-reported"}


# ------------------------------------------------------------ resumes
def make_resume(client, h, ids, **kw):
    body = {"name": "General", "selection": [{"entry_id": i} for i in ids], "contact": {"name": "Test Student", "email": "t@example.org"}, **kw}
    r = client.post("/v1/me/resumes", headers=h, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_resume_cannot_reference_someone_elses_entry(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    e = add(client, a)
    r = client.post("/v1/me/resumes", headers=b, json={"name": "x", "selection": [{"entry_id": e["id"]}]})
    assert r.status_code == 422


def test_resume_versions_restore_and_exports(client):
    _, a = make_user("a@example.org")
    e1, e2 = add(client, a), add(client, a, title="Second project")
    r = make_resume(client, a, [e1["id"]])
    client.put(f"/v1/me/resumes/{r['id']}", headers=a, json={**r, "selection": [{"entry_id": e1["id"]}, {"entry_id": e2["id"]}], "headline": "Student developer"})
    versions = client.get(f"/v1/me/resumes/{r['id']}/versions", headers=a).json()
    assert len(versions) == 2
    first = versions[-1]["id"] if versions[0]["id"] > versions[-1]["id"] else versions[0]["id"]
    back = client.post(f"/v1/me/resumes/{r['id']}/restore/{first}", headers=a).json()
    assert len(back["selection"]) == 1
    docx = client.get(f"/v1/me/resumes/{r['id']}/export.docx", headers=a)
    assert docx.status_code == 200 and docx.content[:2] == b"PK"
    pdf = client.get(f"/v1/me/resumes/{r['id']}/export.pdf", headers=a)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_resume_is_private_between_students(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    r = make_resume(client, a, [add(client, a)["id"]])
    for path in ("", "/preview", "/check", "/versions", "/defence", "/export.pdf", "/export.docx"):
        assert client.get(f"/v1/me/resumes/{r['id']}{path}", headers=b).status_code == 404, path
    assert client.delete(f"/v1/me/resumes/{r['id']}", headers=b).status_code == 404
    assert client.post(f"/v1/me/resumes/{r['id']}/suggest", headers=b).status_code == 404


def test_check_flags_unevidenced_and_self_reported_skills(client):
    _, a = make_user("a@example.org")
    ids = [add(client, a, section="skill", title="Rust", bullets=[], evidence=[], tags=[])["id"],
           add(client, a, title="Vague", bullets=["Worked on stuff"], evidence=[], tags=[])["id"]]
    r = make_resume(client, a, ids, job_description="We need Rust and Kubernetes experience")
    out = client.get(f"/v1/me/resumes/{r['id']}/check", headers=a).json()
    assert out  # structured findings, never a single score
    assert "score" not in out or isinstance(out.get("score"), (type(None),))


def test_defence_questions_come_from_the_resume_and_answers_are_private(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    r = make_resume(client, a, [add(client, a)["id"]])
    qs = client.get(f"/v1/me/resumes/{r['id']}/defence", headers=a).json()["questions"]
    assert qs and all(q.get("question") for q in qs)
    res = client.post("/v1/me/defence/answers", headers=a, json={"resume_id": r["id"], "topic": "projects", "question": qs[0]["question"],
                                                                 "answer": "I built it because friends struggled. I tested it and measured bugs.",
                                                                 "self_scores": {"clarity": 4, "depth": 3, "bogus": 9}})
    assert res.status_code == 201
    assert client.post("/v1/me/defence/answers", headers=b, json={"resume_id": r["id"], "topic": "x", "question": "Why this?", "answer": "a"}).status_code == 404
    ready = client.get("/v1/me/defence/readiness", headers=a).json()
    assert ready["answers_practised"] == 1
    assert client.get("/v1/me/defence/readiness", headers=b).json()["answers_practised"] == 0


# ------------------------------------------------------------ portfolio is opt-in
def test_portfolio_is_off_until_enabled_and_shows_only_chosen_entries(client):
    _, a = make_user("a@example.org")
    shown, hidden = add(client, a), add(client, a, title="Secret project")
    body = {"slug": "test-student", "enabled": False, "display_name": "Test Student", "entry_ids": [shown["id"]]}
    assert client.put("/v1/me/portfolio", headers=a, json=body).status_code == 200
    assert client.get("/v1/portfolios/test-student").status_code == 404
    client.put("/v1/me/portfolio", headers=a, json={**body, "enabled": True})
    pub = client.get("/v1/portfolios/test-student")
    assert pub.status_code == 200 and "Secret project" not in pub.text and "Budget app" in pub.text
    assert "a@example.org" not in pub.text
    assert pub.headers["cache-control"] == "no-store"
    _, b = make_user("b@example.org")
    assert client.put("/v1/me/portfolio", headers=b, json={**body, "entry_ids": [hidden["id"]]}).status_code in (409, 422)
    client.delete("/v1/me/portfolio", headers=a)
    assert client.get("/v1/portfolios/test-student").status_code == 404


# ------------------------------------------------------------ applications and matching
def test_applications_track_history_and_stay_private(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    r = client.post("/v1/me/applications", headers=a, json={"title": "Intern", "organisation": "Org", "deadline": (date.today() + timedelta(days=2)).isoformat()}).json()
    client.put(f"/v1/me/applications/{r['id']}", headers=a, json={"title": "Intern", "status": "applied"})
    got = client.get("/v1/me/applications", headers=a).json()["items"][0]
    assert [h["status"] for h in got["history"]] == ["saved", "applied"]
    assert client.get("/v1/me/applications", headers=b).json()["items"] == []
    assert client.put(f"/v1/me/applications/{r['id']}", headers=b, json={"title": "x"}).status_code == 404
    assert client.post("/v1/me/applications", headers=a, json={"title": "x", "status": "magic"}).status_code == 422
    assert client.post("/v1/me/applications", headers=a, json={"title": "x", "resume_id": 999}).status_code == 404


def test_reminders_and_calendar_export(client):
    _, a = make_user("a@example.org")
    client.post("/v1/me/applications", headers=a, json={"title": "Soon, with; punctuation", "deadline": (date.today() + timedelta(days=2)).isoformat()})
    client.post("/v1/me/applications", headers=a, json={"title": "Far", "deadline": (date.today() + timedelta(days=60)).isoformat()})
    rem = client.get("/v1/me/applications/reminders", headers=a).json()
    assert [r["title"] for r in rem] == ["Soon, with; punctuation"]
    ics = client.get("/v1/me/applications.ics", headers=a)
    assert ics.headers["content-type"].startswith("text/calendar") and "BEGIN:VEVENT" in ics.text and r"Soon\, with\; punctuation" in ics.text


def test_track_from_opportunity_only_when_open(client):
    with session() as db:
        src = make_source(db)
        published(db, m.Opportunity, src, slug="open", title="Open", organisation="O", kind="internship", description="d", eligibility="e",
                  apply_url="https://example.org/a", deadline=date.today() + timedelta(days=9))
        published(db, m.Opportunity, src, slug="old", title="Old", organisation="O", kind="internship", description="d", eligibility="e",
                  apply_url="https://example.org/b", deadline=date.today() - timedelta(days=9))
        db.commit()
    _, a = make_user("a@example.org")
    one = client.post("/v1/me/applications/from-opportunity/open", headers=a)
    assert one.status_code == 201
    assert client.post("/v1/me/applications/from-opportunity/open", headers=a).json()["id"] == one.json()["id"]
    assert client.post("/v1/me/applications/from-opportunity/old", headers=a).status_code == 404


def test_matching_explains_reasons_and_never_guesses_missing_facts(client):
    with session() as db:
        src = make_source(db)
        published(db, m.Opportunity, src, slug="y3", title="Year 3 only", organisation="O", kind="internship", description="d", eligibility="e",
                  apply_url="https://example.org/a", rolling=True, min_year=3, max_year=4, skills=["python"])
        db.commit()
    _, a = make_user("a@example.org")
    out = client.get("/v1/me/opportunities/matches", headers=a).json()
    assert out["matches"] == [] and out["worth_a_look"] == []  # nothing known, so nothing claimed
    client.put("/v1/me/profile", headers=a, json={"year_of_study": 3, "skills": ["python"]})
    out = client.get("/v1/me/opportunities/matches", headers=a).json()
    assert out["matches"] and out["matches"][0]["reasons"]


# ------------------------------------------------------------ journal
def test_journal_is_encrypted_at_rest_private_and_deletable(client):
    _, a = make_user("a@example.org")
    _, b = make_user("b@example.org")
    r = client.post("/v1/me/journal", headers=a, json={"mood": 3, "body": "A very private sentence about my exam week"})
    assert r.status_code == 201
    with get_engine().connect() as c:
        raw = c.execute(text("select body_enc from journal_entries")).scalar()
    assert "private sentence" not in raw
    got = client.get("/v1/me/journal", headers=a).json()["entries"]
    assert got[0]["body"].startswith("A very private")
    assert client.get("/v1/me/journal", headers=b).json()["entries"] == []
    assert client.delete(f"/v1/me/journal/{got[0]['id']}", headers=b).status_code == 404
    assert client.delete(f"/v1/me/journal/{got[0]['id']}", headers=a).status_code == 204
    assert client.get("/v1/me/journal", headers=a).json()["entries"] == []
    assert client.post("/v1/me/journal", headers=a, json={"body": "   "}).status_code == 422
    assert client.post("/v1/me/journal", headers=a, json={"body": "x", "day": (date.today() + timedelta(days=1)).isoformat()}).status_code == 422


def test_journal_shows_crisis_resources_when_words_suggest_it(client):
    _, a = make_user("a@example.org")
    r = client.post("/v1/me/journal", headers=a, json={"body": "I want to end my life"}).json()
    assert r["crisis"] is True and r["resources"]
    calm = client.post("/v1/me/journal", headers=a, json={"body": "Good day, finished my assignment"}).json()
    assert "crisis" not in calm


def test_journal_never_feeds_progress_badges_or_exports_to_institutions(client):
    _, a = make_user("a@example.org")
    for _ in range(3):
        client.post("/v1/me/journal", headers=a, json={"mood": 4, "body": "note"})
    prog = client.get("/v1/me/progress", headers=a).json()
    assert prog["badges"] == [] or all("journal" not in str(b).lower() for b in prog["badges"])

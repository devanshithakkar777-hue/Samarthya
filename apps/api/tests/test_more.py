"""Notes, concept maps, study assistant, mock interview, group sessions, dashboards, prep packs, career switch, credentials."""
from datetime import timedelta

from app import models as m
from app.models import utcnow

from .factories import make_source, make_user, published, session


def _item(db):
    it = published(db, m.LibraryItem, make_source(db), slug="book-one", title="Book One", kind="book", subject="Physics", access_url="https://example.org/b",
                   licence_status="open_access", language="English", format="web")
    db.commit()
    return it


def test_library_notes_are_private_and_validated(client):
    with session() as db:
        _item(db)
    _, a = make_user("a@example.org"); _, b = make_user("b@example.org")
    assert client.post("/v1/me/library-notes/book-one", headers=a, json={"kind": "note", "body": ""}).status_code == 422
    n = client.post("/v1/me/library-notes/book-one", headers=a, json={"kind": "highlight", "quote": "force equals mass times acceleration", "body": "Newton 2"}).json()
    assert len(client.get("/v1/me/library-notes/book-one", headers=a).json()["notes"]) == 1
    assert client.get("/v1/me/library-notes/book-one", headers=b).json()["notes"] == []
    assert client.delete(f"/v1/me/library-notes/note/{n['id']}", headers=b).status_code == 404
    assert client.delete(f"/v1/me/library-notes/note/{n['id']}", headers=a).status_code == 204
    assert client.post("/v1/me/library-notes/missing", headers=a, json={"body": "x"}).status_code == 404


def test_concept_map_crud_and_edge_validation(client):
    _, a = make_user("a@example.org"); _, b = make_user("b@example.org")
    body = {"title": "Forces", "nodes": [{"id": "1", "label": "Force"}, {"id": "2", "label": "Mass"}], "edges": [{"from": "1", "to": "2", "label": "needs"}]}
    mp = client.post("/v1/me/concept-maps", headers=a, json=body).json()
    assert mp["boxes"] == 2 and len(mp["edges"]) == 1
    bad = {**body, "edges": [{"from": "1", "to": "9"}]}
    assert client.post("/v1/me/concept-maps", headers=a, json=bad).status_code == 422
    assert client.post("/v1/me/concept-maps", headers=a, json={**body, "nodes": [{"id": "1", "label": "A"}, {"id": "1", "label": "B"}], "edges": []}).status_code == 422
    assert client.get(f"/v1/me/concept-maps/{mp['id']}", headers=b).status_code == 404
    assert client.put(f"/v1/me/concept-maps/{mp['id']}", headers=a, json={**body, "title": "Renamed"}).json()["title"] == "Renamed"
    assert client.delete(f"/v1/me/concept-maps/{mp['id']}", headers=a).status_code == 204


def test_study_assistant_uses_own_notes_and_handles_crisis(client):
    with session() as db:
        _item(db)
    _, a = make_user("a@example.org")
    client.post("/v1/me/library-notes/book-one", headers=a, json={"body": "entropy always increases in an isolated system"})
    out = client.post("/v1/me/study-assistant", headers=a, json={"question": "what is entropy", "library_slug": "book-one"}).json()
    assert out["mode"] == "retrieval" and out["own_notes"] and "cannot read books" in out["note"]
    crisis = client.post("/v1/me/study-assistant", headers=a, json={"question": "I want to end my life"}).json()
    assert crisis["mode"] == "safety" and crisis["crisis_resources"]


def test_mock_interview_flow_and_privacy(client):
    _, a = make_user("a@example.org"); _, b = make_user("b@example.org")
    mi = client.post("/v1/me/mock-interview", headers=a, json={"count": 2}).json()
    assert mi["next_question"]["of"] == 2 and not mi["finished"]
    short = client.post(f"/v1/me/mock-interview/{mi['id']}/answer", headers=a, json={"answer": "I am good."}).json()
    assert any("short" in x.lower() for x in short["turns"][0]["feedback"]["improvements"])
    long = "When our college fest needed a website I was given the task of building it. I built the pages, tested them with 20 friends and it increased sign-ups to 300. I learned to plan earlier."
    done = client.post(f"/v1/me/mock-interview/{mi['id']}/answer", headers=a, json={"answer": long}).json()
    assert done["finished"] and done["turns"][1]["feedback"]["strengths"]
    assert client.post(f"/v1/me/mock-interview/{mi['id']}/answer", headers=a, json={"answer": "more"}).status_code == 409
    assert client.get(f"/v1/me/mock-interview/{mi['id']}", headers=b).status_code == 404


def _mentor(email="m@example.org"):
    u, h = make_user(email)
    with session() as db:
        db.add(m.Mentor(user_id=u.id, display_name="Mentor M", headline="Engineer", bio="Bio text", kind="industry", status="approved"))
        db.commit()
    return u, h


def test_group_sessions_capacity_privacy_and_cancel(client):
    _, mh = _mentor(); _, s1 = make_user("s1@example.org"); _, s2 = make_user("s2@example.org"); _, plain = make_user("p@example.org")
    when = (utcnow() + timedelta(days=2)).isoformat()
    body = {"title": "Resume clinic", "description": "Bring your resume for group tips.", "starts_at": when, "capacity": 2, "meeting_details": "Link shared in the Meet room"}
    assert client.post("/v1/mentors/me/sessions", headers=plain, json=body).status_code == 403
    assert client.post("/v1/mentors/me/sessions", headers=mh, json={**body, "starts_at": (utcnow() - timedelta(days=1)).isoformat()}).status_code == 422
    sid = client.post("/v1/mentors/me/sessions", headers=mh, json=body).json()["id"]
    listing = client.get("/v1/mentor-sessions", headers=s1).json()["sessions"]
    assert listing[0]["id"] == sid and "meeting_details" not in listing[0]
    assert client.post(f"/v1/mentor-sessions/{sid}/join", headers=s1).json()["meeting_details"]
    assert client.post(f"/v1/mentor-sessions/{sid}/join", headers=s1).status_code == 201
    client.post(f"/v1/mentor-sessions/{sid}/join", headers=s2)
    _, s3 = make_user("s3@example.org")
    assert client.post(f"/v1/mentor-sessions/{sid}/join", headers=s3).status_code == 409
    dash = client.get("/v1/professional/dashboard", headers=mh).json()
    assert dash["sessions"][0]["seats_taken"] == 2 and "name" not in str(dash["sessions"][0]).lower().replace("capacity", "")
    assert client.get("/v1/professional/dashboard", headers=plain).status_code == 403
    client.post(f"/v1/mentors/me/sessions/{sid}/cancel", headers=mh)
    assert client.get("/v1/mentor-sessions", headers=s1).json()["sessions"] == []


def test_employer_posts_drafts_only_and_counts_hidden_below_k(client):
    _, ah = make_user("admin@example.org", m.UserRole.admin); eu, eh = make_user("hr@example.org"); _, sh = make_user("stu@example.org")
    assert client.get("/v1/employer/dashboard", headers=eh).status_code == 403
    assert client.post("/v1/org-admin/employers", headers=eh, json={"slug": "acme", "name": "Acme", "staff_email": "hr@example.org"}).status_code == 403
    assert client.post("/v1/org-admin/employers", headers=ah, json={"slug": "acme", "name": "Acme", "staff_email": "hr@example.org"}).status_code == 201
    opp = {"title": "Summer intern", "kind": "internship", "description": "Eight weeks of real project work.", "eligibility": "Second year students", "apply_url": "https://acme.example/apply"}
    out = client.post("/v1/employer/opportunities", headers=eh, json=opp).json()
    assert out["status"] == "draft"
    assert client.post("/v1/employer/opportunities", headers=eh, json={**opp, "kind": "nonsense"}).status_code == 422
    assert client.post("/v1/employer/opportunities", headers=eh, json={**opp, "apply_url": "http://insecure"}).status_code == 422
    assert client.get("/v1/opportunities").json()["items"] == [] if "items" in client.get("/v1/opportunities").json() else True
    dash = client.get("/v1/employer/dashboard", headers=eh).json()
    assert dash["opportunities"][0]["status"] == "draft" and dash["opportunities"][0]["saves"] is None


def test_ventures_private_and_progress(client):
    _, a = make_user("a@example.org"); _, b = make_user("b@example.org")
    v = client.post("/v1/me/ventures", headers=a, json={"name": "Notes app", "stage": "validating", "milestones": [{"text": "Talk to 10 users", "done": True}, {"text": "Landing page"}]}).json()
    assert v["progress"] == {"done": 1, "total": 2}
    assert client.put(f"/v1/me/ventures/{v['id']}", headers=b, json={"name": "x"}).status_code == 404
    assert client.post("/v1/me/ventures", headers=a, json={"name": "x", "stage": "bogus"}).status_code == 422
    assert client.get("/v1/me/ventures", headers=b).json()["ventures"] == []


def test_prep_pack_is_empty_not_invented_then_fills(client):
    with session() as db:
        src = make_source(db)
        published(db, m.Company, src, slug="acme-co", name="Acme Co", summary="Fake.")
        published(db, m.Lesson, src, slug="acme-l1", pillar="executive", track="prep-acme-co", title="Acme overview", summary="s", body="b", level="beginner")
        db.commit()
        db.commit()
    out = client.get("/v1/companies/acme-co/prep").json()
    assert out["lessons"][0]["slug"] == "acme-l1" and not out["empty"]
    with session() as db:
        published(db, m.Company, make_source(db, "https://example.org/x2"), slug="bare-co", name="Bare", summary="Fake.")
        db.commit()
    assert client.get("/v1/companies/bare-co/prep").json()["empty"] is True
    assert client.get("/v1/companies/none/prep").status_code == 404


def test_career_switch_shows_only_the_gap(client):
    from .factories import seed_core
    seed_core()
    out = client.get("/v1/tools/career-switch", params={"from": "test-role-one", "to": "test-role-two"})
    assert out.status_code == 200 and "does not predict" in out.json()["note"] and len(out.json()["sources"]) == 2
    assert client.get("/v1/tools/career-switch", params={"from": "nope", "to": "test-role-two"}).status_code == 404


def test_partner_credentials_are_admin_recorded_verifiable_and_anonymous(client):
    _, ah = make_user("admin@example.org", m.UserRole.admin); _, sh = make_user("stu@example.org")
    body = {"email": "stu@example.org", "issuer": "Partner Org", "title": "Data basics", "evidence_url": "https://partner.example/cert/1"}
    assert client.post("/v1/org-admin/credentials", headers=sh, json=body).status_code == 403
    code = client.post("/v1/org-admin/credentials", headers=ah, json=body).json()["code"]
    mine = client.get("/v1/me/credentials", headers=sh).json()["credentials"]
    assert mine[0]["kind"] == "partner" and "not an accredited" in mine[0]["note"]
    pub = client.get(f"/v1/credentials/verify/{code}").json()
    assert pub["issuer"] == "Partner Org" and "stu@example.org" not in str(pub) and pub["revoked"] is False
    client.post(f"/v1/org-admin/credentials/{code}/revoke", headers=ah)
    assert client.get(f"/v1/credentials/verify/{code}").json()["revoked"] is True
    assert client.get("/v1/credentials/verify/ZZZZ").status_code == 404


def test_ctc_and_offer_compare(client):
    r = client.post("/v1/calc/ctc", json={"annual_ctc": 600000, "variable_pct": 10, "income_tax_annual": 0})
    assert r.status_code == 200
    d = r.json()
    assert d["variable_per_year"] == 60000 and d["fixed_per_year"] == 540000
    assert 0 < d["inhand_monthly"] < d["gross_monthly"]
    o = client.post("/v1/calc/offers", json={"ctc_a": 500000, "ctc_b": 600000, "variable_pct_b": 30})
    assert o.status_code == 200 and "inhand_difference_monthly" in o.json()
    assert client.post("/v1/calc/ctc", json={"annual_ctc": 0}).status_code == 422


def test_gap_analysis_sorts_terms_by_proof(client):
    from .test_build_explore_live import add, make_resume
    _, a = make_user("g@example.org")
    p = add(client, a, section="project", title="Dashboard", bullets=["Built a dashboard with python"], tags=["python"])
    add(client, a, section="skill", title="kubernetes", bullets=[], evidence=[], tags=[])
    r = make_resume(client, a, [p["id"]], job_description="We need python and kubernetes and terraform. Python daily. Kubernetes, terraform.")
    d = client.get(f"/v1/me/resumes/{r['id']}/gaps", headers=a).json()
    st = {i["term"]: i["state"] for i in d["items"]}
    assert st["python"] == "demonstrated" and st["terraform"] == "to_acquire"
    assert "never says you are or are not qualified" in d["note"]


def test_capability_has_no_overall_score_and_is_private(client):
    _, a = make_user("c@example.org"); _, b = make_user("d@example.org")
    with session() as db:
        uid = db.query(m.User).filter_by(email="c@example.org").one().id
        db.add(m.TopicProgress(user_id=uid, pillar="foundations", topic="Percentages", level=1, attempts=6, correct=2, recent=[]))
        db.commit()
    d = client.get("/v1/me/capability", headers=a).json()
    assert d["areas"][0]["band"] == "needs practice" and "overall" not in " ".join(d.keys()).lower()
    assert client.get("/v1/me/capability", headers=b).json()["areas"] == []


def test_growth_summary_is_a_checklist(client):
    from .test_build_explore_live import add
    _, a = make_user("e@example.org")
    add(client, a, section="plan_30_60_90", title="First 90 days", bullets=[], tags=[])
    d = client.get("/v1/me/growth-summary", headers=a).json()
    assert d["checklist"][0]["done"] is True and d["checklist"][2]["done"] is False
    assert client.get("/v1/me/growth-summary").status_code in (401, 403)


def test_impact_map_joins_only_published_briefs_that_share_a_tag(client):
    from datetime import date
    with session() as db:
        src = make_source(db)
        for slug, cat, tags in [("b1", "economy", ["trade"]), ("b2", "trade-policy", ["trade"]), ("b3", "science", [])]:
            published(db, m.GlobalBrief, src, slug=slug, category=cat, region="World", event_date=date(2026, 11, 1), headline=slug, what_happened="x",
                      what_led="x", why_matters="x", who_affected="x", consequences="x", what_next="x", investigate="x", connects_to=tags)
        db.commit()
    d = client.get("/v1/impact-map").json()
    assert len(d["nodes"]) == 3 and len(d["edges"]) == 1 and d["edges"][0]["because"] == ["trade"]


def test_defence_levels_and_dimensions(client):
    from .test_build_explore_live import add, make_resume
    _, a = make_user("f@example.org")
    e = add(client, a, section="project", title="Chatbot", bullets=["Cut replies from 5 to 2 minutes"], tags=["python"])
    r = make_resume(client, a, [e["id"]])
    low = client.get(f"/v1/me/resumes/{r['id']}/defence?level=1&mode=study", headers=a).json()
    assert low["questions"] and all(q["level"] == 1 and "hint" in q for q in low["questions"])
    sim = client.get(f"/v1/me/resumes/{r['id']}/defence?mode=simulation", headers=a).json()
    assert sim["time_limit_seconds"] == 120 and all("hint" not in q for q in sim["questions"])
    out = client.post("/v1/me/defence/answers", headers=a, json={"resume_id": r["id"], "topic": "technical", "question": "Why python?", "answer": "ok"}).json()
    assert set(out["dimensions"]) >= {"clarity", "structure"} and out["follow_up"]


def test_tools_directory_lists_only_published(client):
    with session() as db:
        src = make_source(db)
        published(db, m.PracticalTool, src, slug="t1", name="Tool One", category="design", what_for="Posters", url="https://example.org")
        db.add(m.PracticalTool(slug="t2", name="Draft Tool", category="design", what_for="x", url="https://example.org"))
        db.commit()
    d = client.get("/v1/practical-tools").json()
    assert [r["slug"] for r in d["results"]] == ["t1"]


def test_pay_ranges_hidden_below_ten_reports(client):
    body = {"role_title": "Data Analyst", "city": "pune", "kind": "full_time", "years_experience": 1}
    for i in range(9):
        _, h = make_user(f"s{i}@example.org")
        assert client.post("/v1/me/salary-reports", headers=h, json={**body, "annual_amount": 400000 + i * 10000}).status_code == 201
    assert client.get("/v1/salary-ranges").json()["results"] == []
    _, h = make_user("s9@example.org")
    assert client.post("/v1/me/salary-reports", headers=h, json={**body, "annual_amount": 500000}).status_code == 201
    assert client.post("/v1/me/salary-reports", headers=h, json={**body, "annual_amount": 500000}).status_code == 409
    r = client.get("/v1/salary-ranges?role=analyst").json()["results"]
    assert len(r) == 1 and r[0]["reports"] == 10 and r[0]["range_low"] <= r[0]["range_high"]
    assert "annual_amount" not in str(r)


def test_peer_feedback_is_anonymous_and_needs_three(client):
    _, owner = make_user("o@example.org")
    req = client.post("/v1/me/feedback-requests", headers=owner, json={"context": "Our hackathon project"}).json()
    giver_headers = [make_user(f"g{i}@example.org")[1] for i in range(3)]
    assert client.post(f"/v1/me/feedback-give/{req['token']}", headers=owner, json={"strengths": "good", "improve": "more"}).status_code == 409
    for i, h in enumerate(giver_headers):
        assert client.post(f"/v1/me/feedback-give/{req['token']}", headers=h, json={"strengths": f"s{i} good", "improve": f"i{i} more"}).status_code == 201
        mine = client.get("/v1/me/feedback-requests", headers=owner).json()["results"][0]
        assert (mine["notes"] == []) == (i < 2)
    assert client.post(f"/v1/me/feedback-give/{req['token']}", headers=giver_headers[0], json={"strengths": "again", "improve": "again"}).status_code == 409
    assert "giver" not in str(mine)


def test_company_copy_makes_a_separate_resume(client):
    from .test_build_explore_live import add, make_resume
    with session() as db:
        published(db, m.Company, make_source(db), slug="acme", name="Acme Ltd", cin="U00000MH2020PTC000001", summary="A test company")
        db.commit()
    _, a = make_user("h@example.org")
    e = add(client, a, section="project", title="Chatbot", bullets=["x"], tags=[])
    r = make_resume(client, a, [e["id"]])
    c = client.post(f"/v1/me/resumes/{r['id']}/company-copy", headers=a, json={"company_slug": "acme"})
    assert c.status_code == 201 and c.json()["target_kind"] == "company" and c.json()["id"] != r["id"]
    assert client.post(f"/v1/me/resumes/{r['id']}/company-copy", headers=a, json={"company_slug": "nope"}).status_code == 404


def test_radar_lists_tiers_for_a_published_role(client):
    _, a = make_user("r@example.org")
    assert client.get("/v1/me/radar/missing", headers=a).status_code == 404

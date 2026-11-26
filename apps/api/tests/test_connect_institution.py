"""Community safety, mentors, institution privacy, the companion, account deletion and cache rules."""
from sqlalchemy import select, text

from app import models as m
from app.db import get_engine
from .factories import make_user, session


def member(client, email, handle):
    _, h = make_user(email)
    assert client.put("/v1/community/me", headers=h, json={"handle": handle}).status_code == 200
    return h


# ------------------------------------------------------------ community
def test_community_requires_signin_and_a_handle(client):
    assert client.get("/v1/community/boards").status_code == 401
    _, h = make_user("a@example.org")
    assert client.post("/v1/community/boards/careers/posts", headers=h, json={"title": "Hello there", "body": "First post"}).status_code == 403
    for bad in ("ab", "UPPER case", "samarthya_official", "admin"):
        assert client.put("/v1/community/me", headers=h, json={"handle": bad}).status_code == 422
    assert client.put("/v1/community/me", headers=h, json={"handle": "Good_Name"}).json()["handle"] == "good_name"
    _, h2 = make_user("b@example.org")
    assert client.put("/v1/community/me", headers=h2, json={"handle": "good_name"}).status_code == 409


def test_posts_show_handle_never_email_and_block_contact_details(client):
    a = member(client, "a@example.org", "asha")
    pid = client.post("/v1/community/boards/careers/posts", headers=a, json={"title": "Which course?", "body": "Looking for advice on data courses."}).json()["id"]
    got = client.get(f"/v1/community/posts/{pid}", headers=a)
    assert "asha" in got.text and "a@example.org" not in got.text
    assert got.headers["cache-control"] == "no-store"
    for body in ("call me on 98765 43210", "email me at x@y.com", "add me on whatsapp"):
        assert client.post(f"/v1/community/posts/{pid}/replies", headers=a, json={"body": body}).status_code == 422
    assert client.post("/v1/community/boards/nope/posts", headers=a, json={"title": "Hello", "body": "hello there"}).status_code == 404


def test_hourly_posting_limit(client):
    a = member(client, "a@example.org", "asha")
    codes = [client.post("/v1/community/boards/careers/posts", headers=a, json={"title": f"Title {i}", "body": "A normal post body"}).status_code for i in range(12)]
    assert codes[:10] == [201] * 10 and codes[10:] == [429, 429]


def test_three_reports_hide_a_post_and_moderator_decides(client):
    author = member(client, "a@example.org", "asha")
    pid = client.post("/v1/community/boards/debate/posts", headers=author, json={"title": "Heated topic", "body": "Something borderline"}).json()["id"]
    for i in range(3):
        r = member(client, f"r{i}@example.org", f"reporter{i}")
        assert client.post("/v1/community/reports", headers=r, json={"kind": "post", "target_id": pid, "reason": "rude"}).status_code == 201
    assert client.get(f"/v1/community/posts/{pid}", headers=author).status_code == 404
    assert client.get("/v1/community/boards/debate/posts", headers=author).json() == []
    _, mod = make_user("mod@example.org", m.UserRole.reviewer)
    reports = client.get("/v1/moderation/reports", headers=mod).json()
    assert reports and reports[0]["status"] == "hidden"
    assert client.post(f"/v1/moderation/reports/{reports[0]['id']}", headers=mod, json={"action": "restore"}).status_code == 200
    assert client.get(f"/v1/community/posts/{pid}", headers=author).status_code == 200
    assert client.get("/v1/moderation/reports", headers=author).status_code == 403


def test_one_person_cannot_hide_a_post_alone_and_reports_dedupe(client):
    author = member(client, "a@example.org", "asha")
    pid = client.post("/v1/community/boards/debate/posts", headers=author, json={"title": "A fine post", "body": "Perfectly fine"}).json()["id"]
    r = member(client, "r@example.org", "reporter")
    for _ in range(5):
        client.post("/v1/community/reports", headers=r, json={"kind": "post", "target_id": pid, "reason": "spam"})
    assert client.get(f"/v1/community/posts/{pid}", headers=author).status_code == 200


def test_only_the_author_can_delete_their_post(client):
    a, b = member(client, "a@example.org", "asha"), member(client, "b@example.org", "bela")
    pid = client.post("/v1/community/boards/careers/posts", headers=a, json={"title": "Mine here", "body": "My own post"}).json()["id"]
    assert client.delete(f"/v1/community/posts/{pid}", headers=b).status_code == 404
    assert client.delete(f"/v1/community/posts/{pid}", headers=a).status_code == 204


def test_distress_in_a_post_returns_helplines(client):
    a = member(client, "a@example.org", "asha")
    r = client.post("/v1/community/boards/campus-life/posts", headers=a, json={"title": "Feeling low", "body": "I want to end my life"}).json()
    assert r["resources"]


# ------------------------------------------------------------ mentors
MENTOR = {"display_name": "Test Mentor", "headline": "Engineer", "bio": "I mentor students on first jobs in software.", "kind": "industry",
          "expertise": ["software"], "languages": ["English"], "profile_url": "https://example.org/mentor"}


def test_mentor_is_hidden_until_approved_by_someone_else(client):
    _, mh = make_user("mentor@example.org")
    assert client.put("/v1/mentors/me", headers=mh, json=MENTOR).json()["status"] == "pending"
    s = member(client, "s@example.org", "stu")
    assert client.get("/v1/mentors", headers=s).json()["mentors"] == []
    bad = {**MENTOR, "profile_url": "http://x.example.org"}
    assert client.put("/v1/mentors/me", headers=mh, json=bad).status_code == 422
    assert client.put("/v1/mentors/me", headers=mh, json={**MENTOR, "bio": "Reach me on 98765 43210 anytime please"}).status_code == 422
    _, rv = make_user("rv@example.org", m.UserRole.reviewer)
    mid = client.get("/v1/moderation/mentors/pending", headers=rv).json()[0]["id"]
    assert client.post(f"/v1/moderation/mentors/{mid}", headers=mh, json={"decision": "approve"}).status_code == 403
    assert client.post(f"/v1/moderation/mentors/{mid}", headers=rv, json={"decision": "approve"}).status_code == 200
    assert len(client.get("/v1/mentors", headers=s).json()["mentors"]) == 1
    # editing sends the profile back for review
    client.put("/v1/mentors/me", headers=mh, json={**MENTOR, "headline": "Senior engineer"})
    assert client.get("/v1/mentors", headers=s).json()["mentors"] == []


def test_a_reviewer_cannot_approve_their_own_mentor_profile(client):
    _, rv = make_user("rv@example.org", m.UserRole.reviewer)
    client.put("/v1/mentors/me", headers=rv, json=MENTOR)
    assert client.post(f"/v1/moderation/mentors/{rv and 1}", headers=rv, json={"decision": "approve"}).status_code == 403


def approved_mentor(client):
    _, mh = make_user("mentor@example.org")
    client.put("/v1/mentors/me", headers=mh, json=MENTOR)
    _, rv = make_user("rv@example.org", m.UserRole.reviewer)
    mid = client.get("/v1/moderation/mentors/pending", headers=rv).json()[0]["id"]
    client.post(f"/v1/moderation/mentors/{mid}", headers=rv, json={"decision": "approve"})
    return mh, mid


def test_mentor_request_shares_contact_only_after_acceptance_and_only_if_chosen(client):
    mh, mid = approved_mentor(client)
    s = member(client, "s@example.org", "stu")
    msg = "Hello, I am a second year student interested in software careers and would value your advice."
    rid = client.post(f"/v1/mentors/{mid}/requests", headers=s, json={"message": msg, "share_contact": "student@example.org"}).json()["id"]
    got = client.get("/v1/mentors/requests/received", headers=mh).json()[0]
    assert got["from"] == "stu" and got["contact"] is None and "s@example.org" not in str(got)
    assert client.post(f"/v1/mentors/{mid}/requests", headers=s, json={"message": msg}).status_code == 409
    assert client.post(f"/v1/mentors/requests/{rid}/respond", headers=s, json={"action": "accept"}).status_code == 404
    client.post(f"/v1/mentors/requests/{rid}/respond", headers=mh, json={"action": "accept", "reply": "Happy to help."})
    assert client.get("/v1/mentors/requests/received", headers=mh).json()[0]["contact"] == "student@example.org"
    assert client.get("/v1/mentors/requests/sent", headers=s).json()[0]["status"] == "accepted"
    assert client.get("/v1/mentors/requests/received", headers=s).status_code == 403


def test_mentor_request_rejects_contact_details_in_message_and_self_requests(client):
    mh, mid = approved_mentor(client)
    s = member(client, "s@example.org", "stu")
    assert client.post(f"/v1/mentors/{mid}/requests", headers=s, json={"message": "Please call me on 98765 43210 about my career plans"}).status_code == 422
    assert client.post(f"/v1/mentors/{mid}/requests", headers=mh, json={"message": "x" * 30}).status_code == 422


# ------------------------------------------------------------ institutions
def make_institution(client):
    _, adm = make_user("admin@example.org", m.UserRole.admin)
    r = client.post("/v1/org-admin/institutions", headers=adm, json={"name": "Test College", "slug": "test-college"}).json()
    return adm, r


def test_join_code_is_hashed_and_staff_need_assignment(client):
    adm, inst = make_institution(client)
    with session() as db:
        row = db.scalar(select(m.Institution))
        assert inst["join_code"] not in row.join_code_hash and inst["join_code"] not in str(row.__dict__)
    _, staff = make_user("staff@example.org")
    assert client.get("/v1/institution/test-college/overview", headers=staff).status_code == 404
    client.post(f"/v1/org-admin/institutions/{inst['id']}/staff", headers=adm, json={"email": "staff@example.org", "role": "placement"})
    assert client.get("/v1/institution/test-college/overview", headers=staff).status_code == 200
    _, st = make_user("s@example.org")
    assert client.post("/v1/me/institution/join", headers=st, json={"code": "WRONGCODE"}).status_code == 404
    new = client.post(f"/v1/org-admin/institutions/{inst['id']}/rotate-code", headers=adm).json()["join_code"]
    assert client.post("/v1/me/institution/join", headers=st, json={"code": inst["join_code"]}).status_code == 404
    assert client.post("/v1/me/institution/join", headers=st, json={"code": new}).status_code == 200
    assert client.post("/v1/org-admin/institutions", headers=st, json={"name": "x", "slug": "xx"}).status_code == 403


def test_institution_sees_nothing_below_ten_sharing_students(client):
    adm, inst = make_institution(client)
    _, staff = make_user("staff@example.org")
    client.post(f"/v1/org-admin/institutions/{inst['id']}/staff", headers=adm, json={"email": "staff@example.org"})
    for i in range(9):
        _, h = make_user(f"s{i}@example.org")
        client.post("/v1/me/institution/join", headers=h, json={"code": inst["join_code"], "share_readiness": True})
        client.post("/v1/me/master", headers=h, json={"section": "skill", "title": "x"})
    out = client.get("/v1/institution/test-college/overview", headers=staff).json()
    assert out["suppressed"] is True and "has_profile" not in out
    _, h = make_user("s9@example.org")
    client.post("/v1/me/institution/join", headers=h, json={"code": inst["join_code"], "share_readiness": True})
    out = client.get("/v1/institution/test-college/overview", headers=staff).json()
    assert out["suppressed"] is False and out["has_profile"] == 90
    # a student who switches sharing off drops the count back under the threshold
    client.put("/v1/me/institution", headers=h, json={"share_readiness": False})
    assert client.get("/v1/institution/test-college/overview", headers=staff).json()["suppressed"] is True


def test_institution_view_contains_no_individual_or_wellness_data(client):
    adm, inst = make_institution(client)
    _, staff = make_user("staff@example.org")
    client.post(f"/v1/org-admin/institutions/{inst['id']}/staff", headers=adm, json={"email": "staff@example.org"})
    for i in range(10):
        _, h = make_user(f"s{i}@example.org")
        client.post("/v1/me/institution/join", headers=h, json={"code": inst["join_code"], "share_readiness": True})
        client.post("/v1/me/journal", headers=h, json={"mood": 1, "body": "SECRETJOURNALTEXT"})
    text_out = client.get("/v1/institution/test-college/overview", headers=staff).text.lower()
    for forbidden in ("secretjournaltext", "mood", "journal", "@example.org", "wellness"):
        assert forbidden not in text_out.replace("wellness data is never included", "")


def test_staff_of_one_institution_cannot_see_another(client):
    adm, inst = make_institution(client)
    other = client.post("/v1/org-admin/institutions", headers=adm, json={"name": "Other", "slug": "other"}).json()
    _, staff = make_user("staff@example.org")
    client.post(f"/v1/org-admin/institutions/{other['id']}/staff", headers=adm, json={"email": "staff@example.org"})
    assert client.get("/v1/institution/test-college/overview", headers=staff).status_code == 404
    assert client.get("/v1/institution/other/overview", headers=staff).status_code == 200


# ------------------------------------------------------------ companion
def test_companion_short_circuits_on_distress_and_falls_back_without_ai(client):
    _, a = make_user("a@example.org")
    assert client.get("/v1/me/companion/status", headers=a).json()["ai_enabled"] is False
    r = client.post("/v1/me/companion", headers=a, json={"question": "I want to end my life"}).json()
    assert r["mode"] == "safety" and r["crisis_resources"]
    r = client.post("/v1/me/companion", headers=a, json={"question": "What does an analyst do?"}).json()
    assert r["mode"] == "retrieval"
    assert client.post("/v1/me/companion", json={"question": "hi there"}).status_code == 401


# ------------------------------------------------------------ account deletion and cache rules
def test_deleting_an_account_removes_everything_the_student_owns(client):
    h = member(client, "gone@example.org", "goner")
    client.post("/v1/me/master", headers=h, json={"section": "skill", "title": "x"})
    client.post("/v1/me/journal", headers=h, json={"mood": 3, "body": "bye"})
    client.post("/v1/me/applications", headers=h, json={"title": "App"})
    client.post("/v1/me/decks", headers=h, json={"title": "D"})
    client.post("/v1/community/boards/careers/posts", headers=h, json={"title": "A post", "body": "Some text"})
    client.put("/v1/mentors/me", headers=h, json=MENTOR)
    _, other = make_user("stay@example.org")
    client.post("/v1/me/master", headers=other, json={"section": "skill", "title": "keep"})
    assert client.delete("/v1/me", headers=h).status_code in (200, 204)
    with get_engine().connect() as c:
        for t in ("master_entries", "journal_entries", "applications", "flash_decks", "posts", "mentors", "members"):
            n = c.execute(text(f"select count(*) from {t} where " + ("user_id" if t not in ("posts",) else "author_id") + " = 1")).scalar()
            assert n == 0, t
        assert c.execute(text("select count(*) from master_entries")).scalar() == 1


def test_private_routes_are_never_cached(client):
    a = member(client, "a@example.org", "asha")
    for path in ("/v1/community/boards", "/v1/mentors", "/v1/me/journal", "/v1/me/master", "/v1/me/institution"):
        assert client.get(path, headers=a).headers["cache-control"] == "no-store", path
    assert "public" in client.get("/v1/lessons").headers["cache-control"]


def test_every_user_route_requires_signin(client):
    for method, path in [("get", "/v1/me/master"), ("get", "/v1/me/resumes"), ("get", "/v1/me/journal"), ("get", "/v1/me/applications"),
                         ("get", "/v1/me/progress"), ("get", "/v1/me/notes"), ("get", "/v1/me/decks"), ("get", "/v1/me/study"),
                         ("get", "/v1/mentors"), ("get", "/v1/community/boards"), ("get", "/v1/me/institution"),
                         ("get", "/v1/me/portfolio"), ("get", "/v1/me/transcript.pdf"), ("get", "/v1/moderation/reports")]:
        assert getattr(client, method)(path).status_code == 401, path

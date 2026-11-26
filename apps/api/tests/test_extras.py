"""Scam checker, interest explorer, opt-in parent view and the extra institution aggregates."""
from .factories import make_user
from .test_connect_institution import make_institution

FEE = "Congratulations you have been selected! Pay Rs 999 registration fee on UPI today only. Contact on WhatsApp hr.jobs@gmail.com"


def test_scam_checker_flags_known_patterns_and_never_says_safe(client):
    out = client.post("/v1/tools/scam-check", json={"text": FEE}).json()
    ids = {f["id"] for f in out["flags"]}
    assert out["verdict"] == "many_flags" and {"fee", "no_interview", "chat_only", "free_mail"} <= ids
    assert all(f["source"].startswith("https://") for f in out["flags"]) and "1930" in out["help"]["report"]
    clean = client.post("/v1/tools/scam-check", json={"text": "Interview for the analyst role is on Monday at our Pune office; bring your CV."}).json()
    assert clean["verdict"] == "none_found" and "does not mean" in clean["summary"]
    assert client.post("/v1/tools/scam-check", json={"text": "short"}).status_code == 422


def test_scam_checker_flags_aicte_lookalike_domain(client):
    out = client.post("/v1/tools/scam-check", json={"text": "Offer letter from AICTE, verify at www.aicte-jobs-portal.com now please"}).json()
    assert "impersonation" in {f["id"] for f in out["flags"]}
    ok = client.post("/v1/tools/scam-check", json={"text": "Register for the AICTE internship at internship.aicte-india.org later this week"}).json()
    assert "impersonation" not in {f["id"] for f in ok["flags"]}


def test_interest_explorer_scores_in_memory(client):
    items = client.get("/v1/tools/interests").json()
    assert len(items["items"]) == 36 and "O*NET" in items["source"]["title"]
    answers = [5 if i % 6 == 3 else 1 for i in range(36)]  # item order cycles R I A S E C, so index%6==3 is Social
    out = client.post("/v1/tools/interests", json={"answers": answers}).json()
    assert out["types"][0]["key"] == "S" and out["code"].startswith("S")
    assert client.post("/v1/tools/interests", json={"answers": [9] * 36}).status_code == 422
    assert client.post("/v1/tools/interests", json={"answers": [3] * 5}).status_code == 422


def test_parent_link_is_opt_in_limited_and_revocable(client):
    _, h = make_user("s@example.org")
    client.post("/v1/me/journal", headers=h, json={"mood": 2, "body": "PRIVATEJOURNAL"})
    client.post("/v1/me/applications", headers=h, json={"title": "SECRETAPP", "organisation": "Org"})
    made = client.post("/v1/me/parent-links", headers=h, json={"label": "Mum", "show_topics": False}).json()
    tok = made["token"]
    view = client.get(f"/v1/parent-view/{tok}")
    assert view.status_code == 200 and view.headers["cache-control"] == "no-store"
    low = view.text.lower()
    for forbidden in ("privatejournal", "secretapp", "mood", "@example.org", "topics"):
        assert forbidden not in low
    row = client.get("/v1/me/parent-links", headers=h).json()["links"][0]
    assert "token" not in row and "token_hash" not in str(row)
    assert client.delete(f"/v1/me/parent-links/{made['id']}", headers=h).status_code == 204
    assert client.get(f"/v1/parent-view/{tok}").status_code == 404
    assert client.get("/v1/parent-view/not-a-real-token").status_code == 404
    _, other = make_user("o@example.org")
    assert client.delete(f"/v1/me/parent-links/{made['id']}", headers=other).status_code == 404
    assert client.get("/v1/me/parent-links").status_code == 401


def test_parent_links_are_capped(client):
    _, h = make_user("s@example.org")
    codes = [client.post("/v1/me/parent-links", headers=h, json={}).status_code for _ in range(4)]
    assert codes == [201, 201, 201, 409]


def test_institution_group_figures_only_for_ten_or_more(client):
    adm, inst = make_institution(client)
    _, staff = make_user("staff@example.org")
    client.post(f"/v1/org-admin/institutions/{inst['id']}/staff", headers=adm, json={"email": "staff@example.org"})
    for i in range(10):
        _, h = make_user(f"s{i}@example.org")
        client.post("/v1/me/institution/join", headers=h, json={"code": inst["join_code"], "share_readiness": True})
        client.post("/v1/me/master", headers=h, json={"section": "skill", "title": "Excel"})
        if i < 4:
            client.post("/v1/me/master", headers=h, json={"section": "skill", "title": "Rare skill"})
    out = client.get("/v1/institution/test-college/overview", headers=staff).json()
    skills = {s["skill"]: s["students"] for s in out["common_skills"]}
    assert skills == {"excel": 10}  # the skill only 4 students list is never shown
    assert "learning_gaps" in out and out["application_stages_students"] == {}


def test_growth_sections_accepted_in_master_profile(client):
    _, h = make_user("s@example.org")
    r = client.post("/v1/me/master", headers=h, json={"section": "workplace_win", "title": "Cut report time"})
    assert r.status_code in (200, 201)

from app import models as m
from app.services.email import OUTBOX
from .factories import make_user, seed_core, session


def sign_in(client, email="student@example.org"):
    client.post("/v1/auth/otp/request", json={"email": email})
    code = OUTBOX[-1]["code"]
    r = client.post("/v1/auth/otp/verify", json={"email": email, "code": code})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, r.json()


def test_otp_sign_in_creates_student(client):
    headers, body = sign_in(client)
    assert body["user"] == {"email": "student@example.org", "role": "student"}
    assert client.get("/v1/me", headers=headers).json()["email"] == "student@example.org"


def test_wrong_code_and_lockout_and_reuse(client):
    client.post("/v1/auth/otp/request", json={"email": "a@example.org"})
    good = OUTBOX[-1]["code"]
    bad = "000000" if good != "000000" else "111111"
    for _ in range(5):
        assert client.post("/v1/auth/otp/verify", json={"email": "a@example.org", "code": bad}).status_code == 400
    assert client.post("/v1/auth/otp/verify", json={"email": "a@example.org", "code": good}).status_code == 429
    client.post("/v1/auth/otp/request", json={"email": "b@example.org"})
    code = OUTBOX[-1]["code"]
    assert client.post("/v1/auth/otp/verify", json={"email": "b@example.org", "code": code}).status_code == 200
    assert client.post("/v1/auth/otp/verify", json={"email": "b@example.org", "code": code}).status_code == 400


def test_code_request_limits_and_same_response(client):
    for _ in range(5):
        assert client.post("/v1/auth/otp/request", json={"email": "c@example.org"}).status_code == 202
    assert client.post("/v1/auth/otp/request", json={"email": "c@example.org"}).status_code == 429
    assert client.post("/v1/auth/otp/request", json={"email": "not-an-email"}).status_code == 422


def test_garbage_and_missing_tokens(client):
    assert client.get("/v1/me").status_code == 401
    assert client.get("/v1/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_profile_fit_and_checklist_round_trip(client):
    ids = seed_core()
    headers, _ = sign_in(client)
    r = client.put("/v1/me/profile", headers=headers, json={
        "qualification": ids["bcom"], "year_of_study": 2, "interests": [ids["s1"]], "skills": []})
    assert r.status_code == 200 and r.json()["qualification"] == ids["bcom"]
    assert client.put("/v1/me/profile", headers=headers, json={"qualification": "nope-degree"}).status_code == 422
    first = client.get("/v1/me/fit", headers=headers).json()["results"][0]
    assert first["role"]["slug"] == ids["role1"] and first["eligibility"]["label"] == "eligible"

    rid = ids["req_ids"][1]
    assert client.put(f"/v1/me/checklist/items/{rid}", headers=headers, json={"status": "done"}).status_code == 200
    items = client.get(f"/v1/me/checklist/{ids['role1']}", headers=headers).json()["items"]
    assert {i["id"]: i["status"] for i in items}[rid] == "done"
    after = client.get("/v1/me/fit", headers=headers).json()["results"][0]
    assert after["readiness"]["by_tier"]["mandatory"]["done"] == 1
    assert client.put("/v1/me/checklist/items/99999", headers=headers, json={"status": "done"}).status_code == 404
    assert client.put(f"/v1/me/checklist/items/{rid}", headers=headers, json={"status": "bogus"}).status_code == 422


def test_saved_items(client):
    seed_core()
    headers, _ = sign_in(client)
    client.post("/v1/me/saved", headers=headers, json={"entity_type": "role", "entity_id": 1})
    client.post("/v1/me/saved", headers=headers, json={"entity_type": "role", "entity_id": 1})
    assert client.get("/v1/me/saved", headers=headers).json() == [{"entity_type": "role", "entity_id": 1}]
    assert client.delete("/v1/me/saved/role/1", headers=headers).status_code == 204
    assert client.get("/v1/me/saved", headers=headers).json() == []


def test_students_cannot_see_each_others_data(client):
    ids = seed_core()
    a, _ = sign_in(client, "a@example.org")
    b, _ = sign_in(client, "b@example.org")
    client.put(f"/v1/me/checklist/items/{ids['req_ids'][0]}", headers=a, json={"status": "done"})
    items = client.get(f"/v1/me/checklist/{ids['role1']}", headers=b).json()["items"]
    assert all(i["status"] == "todo" for i in items)


def test_export_and_account_deletion(client):
    ids = seed_core()
    headers, _ = sign_in(client)
    client.put("/v1/me/profile", headers=headers, json={"qualification": ids["bcom"], "interests": [ids["s1"]]})
    client.put(f"/v1/me/checklist/items/{ids['req_ids'][0]}", headers=headers, json={"status": "done"})
    export = client.get("/v1/me/export", headers=headers).json()
    assert export["account"]["email"] == "student@example.org" and len(export["checklist"]) == 1
    assert client.delete("/v1/me", headers=headers).status_code == 204
    assert client.get("/v1/me", headers=headers).status_code == 401
    with session() as db:
        assert db.query(m.User).filter_by(email="student@example.org").count() == 0
        assert db.query(m.ChecklistProgress).count() == 0 and db.query(m.Profile).count() == 0


def test_deleting_an_editor_keeps_content_history(client):
    ed_user, ed = make_user("ed@example.org", m.UserRole.editor)
    client.post("/v1/admin/sectors", headers=ed, json={"slug": "kept", "name": "n", "summary": "s"})
    assert client.delete("/v1/me", headers=ed).status_code == 204
    with session() as db:
        s = db.query(m.Sector).filter_by(slug="kept").one()
        assert s.created_by_id is None


def test_admin_bootstrap_and_role_change(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "admin_bootstrap_email", "boss@example.org")
    headers, body = sign_in(client, "boss@example.org")
    assert body["user"]["role"] == "admin"
    student, _ = make_user("s@example.org")
    r = client.post(f"/v1/admin/users/{student.id}/role", headers=headers, json={"role": "editor"})
    assert r.status_code == 200 and r.json()["role"] == "editor"
    assert client.post(f"/v1/admin/users/{student.id}/role", headers=headers, json={"role": "king"}).status_code == 422

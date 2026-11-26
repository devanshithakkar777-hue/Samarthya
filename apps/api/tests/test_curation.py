from datetime import date, timedelta

from app import models as m
from .factories import make_user, seed_core, session


def setup_people():
    _, ed = make_user("editor@example.org", m.UserRole.editor)
    _, rv = make_user("reviewer@example.org", m.UserRole.reviewer)
    _, st = make_user("student@example.org", m.UserRole.student)
    return ed, rv, st


def new_source(client, ed, url="https://example.org/s1"):
    r = client.post("/v1/admin/sources", headers=ed, json={
        "url": url, "title": "T", "publisher": "P", "kind": "official"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_students_cannot_use_curation(client):
    _, _, st = setup_people()
    assert client.get("/v1/admin/sectors", headers=st).status_code == 403
    assert client.get("/v1/admin/sectors").status_code == 401


def test_full_publish_flow_and_public_visibility(client):
    ed, rv, _ = setup_people()
    src = new_source(client, ed)
    r = client.post("/v1/admin/sectors", headers=ed, json={"slug": "demo-sector", "name": "Demo", "summary": "s"})
    sid = r.json()["id"]
    assert r.json()["status"] == "draft"
    assert client.get("/v1/sectors/demo-sector").status_code == 404

    # cannot move forward without a source and a verification date
    assert client.post(f"/v1/admin/sectors/{sid}/submit", headers=ed).status_code == 409
    client.patch(f"/v1/admin/sectors/{sid}", headers=ed, json={"source_id": src, "last_verified": date.today().isoformat()})
    assert client.post(f"/v1/admin/sectors/{sid}/submit", headers=ed).json()["status"] == "in_review"

    # editors cannot publish
    assert client.post(f"/v1/admin/sectors/{sid}/approve", headers=ed).status_code == 403
    pub = client.post(f"/v1/admin/sectors/{sid}/approve", headers=rv)
    assert pub.status_code == 200 and pub.json()["status"] == "published"
    detail = client.get("/v1/sectors/demo-sector").json()
    assert detail["source"]["publisher"] == "P" and detail["stale"] is False


def test_reviewer_cannot_approve_own_work(client):
    _, rv, _ = setup_people()
    src = new_source(client, rv)
    sid = client.post("/v1/admin/sectors", headers=rv, json={
        "slug": "mine", "name": "Mine", "summary": "s", "source_id": src,
        "last_verified": date.today().isoformat()}).json()["id"]
    client.post(f"/v1/admin/sectors/{sid}/submit", headers=rv)
    r = client.post(f"/v1/admin/sectors/{sid}/approve", headers=rv)
    assert r.status_code == 403 and "different reviewer" in r.json()["detail"]


def test_role_needs_published_sector_and_requirements(client):
    ed, rv, _ = setup_people()
    src = new_source(client, ed)
    common = {"source_id": src, "last_verified": date.today().isoformat()}
    sid = client.post("/v1/admin/sectors", headers=ed, json={"slug": "s", "name": "S", "summary": "x", **common}).json()["id"]
    rid = client.post("/v1/admin/roles", headers=ed, json={
        "slug": "r", "title": "R", "job_family": "F", "sector_id": sid, "description": "d", **common}).json()["id"]
    client.post(f"/v1/admin/roles/{rid}/submit", headers=ed)
    assert client.post(f"/v1/admin/roles/{rid}/approve", headers=rv).status_code == 409  # sector not published
    client.post(f"/v1/admin/sectors/{sid}/submit", headers=ed)
    client.post(f"/v1/admin/sectors/{sid}/approve", headers=rv)
    assert client.post(f"/v1/admin/roles/{rid}/approve", headers=rv).status_code == 409  # no requirements
    client.post("/v1/admin/role_requirements", headers=ed, json={
        "role_id": rid, "type": "skill", "tier": "mandatory", "label": "Something", "position": 1})
    assert client.post(f"/v1/admin/roles/{rid}/approve", headers=rv).json()["status"] == "published"
    # editing a published role's requirements needs a reviewer
    r = client.post("/v1/admin/role_requirements", headers=ed, json={
        "role_id": rid, "type": "skill", "tier": "recommended", "label": "More"})
    assert r.status_code == 403
    r = client.post("/v1/admin/role_requirements", headers=rv, json={
        "role_id": rid, "type": "skill", "tier": "recommended", "label": "More"})
    assert r.status_code == 201


def test_published_content_is_reviewer_only_to_change(client):
    ed, rv, _ = setup_people()
    ids = seed_core()
    with session() as db:
        sid = db.query(m.Sector).filter_by(slug=ids["s1"]).one().id
    assert client.patch(f"/v1/admin/sectors/{sid}", headers=ed, json={"name": "Hacked"}).status_code == 403
    assert client.patch(f"/v1/admin/sectors/{sid}", headers=rv, json={"name": "Fixed"}).status_code == 200
    assert client.get(f"/v1/sectors/{ids['s1']}").json()["name"] == "Fixed"
    assert client.delete(f"/v1/admin/sectors/{sid}", headers=rv).status_code == 409  # unpublish first


def test_validation_errors_are_clean(client):
    ed, _, _ = setup_people()
    assert client.post("/v1/admin/sectors", headers=ed, json={"slug": "x", "name": "n"}).status_code == 422
    assert client.post("/v1/admin/sectors", headers=ed, json={"slug": "x", "name": "n", "summary": "s",
                                                                 "status": "published"}).status_code == 422
    assert client.post("/v1/admin/roles", headers=ed, json={
        "slug": "r", "title": "R", "job_family": "F", "sector_id": 999, "description": "d"}).status_code == 409
    assert client.post("/v1/admin/nonsense", headers=ed, json={}).status_code == 404
    client.post("/v1/admin/sectors", headers=ed, json={"slug": "dup", "name": "n", "summary": "s"})
    assert client.post("/v1/admin/sectors", headers=ed, json={"slug": "dup", "name": "n", "summary": "s"}).status_code == 409
    assert client.post("/v1/admin/sources", headers=ed, json={
        "url": "u", "title": "t", "publisher": "p", "kind": "bogus"}).status_code == 422


def test_stale_list_and_verify(client):
    ed, rv, _ = setup_people()
    ids = seed_core()
    with session() as db:
        s = db.query(m.Sector).filter_by(slug=ids["s1"]).one()
        s.last_verified = date.today() - timedelta(days=400)
        sid = s.id
        db.commit()
    stale = client.get("/v1/admin/stale", headers=ed).json()
    assert any(i["type"] == "sectors" and i["id"] == sid for i in stale)
    assert client.get(f"/v1/sectors/{ids['s1']}").json()["stale"] is True
    assert client.post(f"/v1/admin/sectors/{sid}/verify", headers=ed).status_code == 403
    assert client.post(f"/v1/admin/sectors/{sid}/verify", headers=rv).status_code == 200
    assert client.get(f"/v1/sectors/{ids['s1']}").json()["stale"] is False


def test_audit_log_records_changes(client):
    ed, _, _ = setup_people()
    client.post("/v1/admin/sectors", headers=ed, json={"slug": "a", "name": "n", "summary": "s"})
    with session() as db:
        assert db.query(m.AuditLog).filter_by(action="create", entity_type="sectors").count() == 1


def test_editor_can_fetch_a_single_item(client):
    ed, _, _ = setup_people()
    r = client.post("/v1/admin/sectors", headers=ed, json={"name": "SAMPLE X", "slug": "sample-x", "summary": "SAMPLE"})
    assert r.status_code == 201, r.text
    got = client.get(f"/v1/admin/sectors/{r.json()['id']}", headers=ed)
    assert got.status_code == 200 and got.json()["slug"] == "sample-x"
    assert client.get("/v1/admin/sectors/99999", headers=ed).status_code == 404

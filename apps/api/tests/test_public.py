from datetime import date

from app import models as m
from .factories import published, seed_core, session


def test_lists_and_details(client):
    ids = seed_core()
    assert [q["slug"] for q in client.get("/v1/qualifications").json()] == [ids["bcom"], ids["btech"]]
    sectors = client.get("/v1/sectors").json()
    assert {s["slug"]: s["role_count"] for s in sectors} == {ids["s1"]: 1, ids["s2"]: 1}
    d = client.get(f"/v1/sectors/{ids['s1']}").json()
    assert d["roles"][0]["slug"] == ids["role1"] and d["education_routes"][0]["strength"] == 3
    role = client.get(f"/v1/roles/{ids['role1']}").json()
    assert [r["label"] for r in role["requirements"]["mandatory"]] == ["Know the test skill", "One internship"]
    assert role["requirements"]["differentiator"][0]["label"] == "A side project"
    assert role["employers"][0]["careers_url"] == "https://example.org/careers"
    assert role["source"]["url"] == "https://example.org/source" and role["last_verified"] == date.today().isoformat()
    assert client.get("/v1/roles/missing").status_code == 404
    co = client.get("/v1/companies/test-company").json()
    assert co["roles"][0]["slug"] == ids["role1"]


def test_skill_resources_label_sponsored_and_sort(client):
    ids = seed_core()
    with session() as db:
        skill = db.query(m.Skill).filter_by(slug=ids["skill"]).one()
        src = db.get(m.Source, ids["src"])
        published(db, m.LearningResource, src, skill_id=skill.id, title="Paid advanced", provider="P", url="https://e.org/1",
                  format="course", level="Advanced", price_inr=999, sponsored=True)
        published(db, m.LearningResource, src, skill_id=skill.id, title="Free beginner", provider="P", url="https://e.org/2",
                  format="video", level="Beginner", price_inr=0)
        db.add(m.LearningResource(skill_id=skill.id, title="Draft", provider="P", url="https://e.org/3",
                                  format="x", level="Beginner", status=m.Status.draft))
        db.commit()
    res = client.get(f"/v1/skills/{ids['skill']}").json()["resources"]
    assert [r["title"] for r in res] == ["Free beginner", "Paid advanced"]
    assert res[0]["free"] is True and res[1]["sponsored"] is True


def test_roadmap_groups_by_year(client):
    ids = seed_core()
    with session() as db:
        src = db.get(m.Source, ids["src"])
        q = db.query(m.Qualification).filter_by(slug=ids["bcom"]).one()
        for year, title in ((2, "Second"), (1, "First")):
            published(db, m.RoadmapStep, src, qualification_id=q.id, year_of_study=year, title=title, detail="d")
        db.commit()
    years = client.get("/v1/roadmap", params={"qualification": ids["bcom"]}).json()["years"]
    assert [(y["year"], y["steps"][0]["title"]) for y in years] == [(1, "First"), (2, "Second")]
    assert client.get("/v1/roadmap", params={"qualification": "nope"}).status_code == 404


def test_briefing_newest_first(client):
    ids = seed_core()
    with session() as db:
        src = db.get(m.Source, ids["src"])
        for d, h in ((date(2026, 1, 1), "Old"), (date(2026, 6, 1), "New")):
            published(db, m.NewsItem, src, headline=h, summary="s", why_it_matters="w", link="https://e.org", event_date=d)
        db.commit()
    assert [n["headline"] for n in client.get("/v1/briefing").json()] == ["New", "Old"]


def test_search_is_safe_and_finds_published_only(client):
    ids = seed_core()
    assert client.get("/v1/search", params={"q": "Test Role"}).json()["roles"][0]["slug"] == ids["role1"]
    assert client.get("/v1/search", params={"q": "%%"}).json() == {"sectors": [], "roles": [], "companies": [], "skills": []}
    assert client.get("/v1/search", params={"q": "a"}).status_code == 422
    assert client.get("/v1/search", params={"q": "x'; drop table roles;--"}).status_code == 200


def test_coverage_reports_real_counts(client):
    seed_core()
    cov = client.get("/v1/coverage").json()
    assert cov["roles"] == 2 and cov["sectors"] == 2 and cov["resources"] == 0


def test_reports_validation_and_limit(client):
    assert client.post("/v1/reports", json={"message": "short"}).status_code == 422
    ok = client.post("/v1/reports", json={"entity_type": "role", "entity_id": 1, "message": "This requirement looks out of date."})
    assert ok.status_code == 201
    assert client.post("/v1/reports", json={"message": "x" * 3000}).status_code == 422
    for _ in range(9):
        client.post("/v1/reports", json={"message": "Another valid problem report."})
    assert client.post("/v1/reports", json={"message": "One too many reports."}).status_code == 429


def test_security_headers_and_caching(client):
    seed_core()
    r = client.get("/v1/sectors")
    assert r.headers["cache-control"] == "public, max-age=60" and r.headers["x-content-type-options"] == "nosniff"
    assert client.get("/healthz").json() == {"ok": True}
    assert client.get("/readyz").json() == {"ok": True}
    me = client.get("/v1/me")
    assert me.headers["cache-control"] == "no-store"


def test_briefing_groups_by_week_and_links_related_roles(client):
    from datetime import date
    from app import models as m
    from .factories import make_source, published, session
    with session() as db:
        src = make_source(db)
        sec = published(db, m.Sector, src, slug="brief-sector", name="Brief Sector", summary="Fake.")
        published(db, m.Role, src, slug="brief-role", title="Brief Role", job_family="F", sector_id=sec.id, description="Fake.")
        published(db, m.NewsItem, src, headline="Fake notice", summary="Fake.", why_it_matters="Fake.",
                  link="https://example.org/n", event_date=date(2026, 11, 26), sector_id=sec.id)
        db.commit()
    item = client.get("/v1/briefing").json()[0]
    assert item["week_of"] == "2026-11-23"
    assert item["related_roles"] == [{"slug": "brief-role", "title": "Brief Role"}]


def test_participation_form_and_admin_only_listing(client):
    from app import models as m
    from .factories import make_user
    ok = client.post("/v1/participate", json={"pathway": "mentor", "contact": "Helper@Example.org", "message": "Happy to help"})
    assert ok.status_code == 201
    assert client.post("/v1/participate", json={"pathway": "nonsense", "contact": "a@example.org"}).status_code == 422
    assert client.post("/v1/participate", json={"pathway": "mentor", "contact": "not-an-email"}).status_code == 422
    _, ed = make_user("pe@example.org", m.UserRole.editor)
    _, ad = make_user("pa@example.org", m.UserRole.admin)
    assert client.get("/v1/admin/participation", headers=ed).status_code == 403
    rows = client.get("/v1/admin/participation", headers=ad).json()
    assert rows[0]["contact"] == "helper@example.org"
    for _ in range(6):
        last = client.post("/v1/participate", json={"pathway": "volunteer", "contact": "x@example.org"})
    assert last.status_code == 429

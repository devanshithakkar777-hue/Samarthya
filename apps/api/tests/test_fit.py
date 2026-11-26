from app import models as m
from .factories import seed_core, session


def fit(client, ids, profile, completed=(), sort="eligibility"):
    r = client.post("/v1/fit", json={"profile": profile, "completed_requirement_ids": list(completed), "sort": sort})
    assert r.status_code == 200, r.text
    return {x["role"]["slug"]: x for x in r.json()["results"]}


def test_four_separate_answers_and_no_score(client):
    ids = seed_core()
    res = fit(client, ids, {"qualification": ids["bcom"], "interests": [ids["s1"]]})
    item = res[ids["role1"]]
    assert set(item) == {"role", "eligibility", "compatibility", "readiness", "opportunity"}
    assert "score" not in str(item).lower()


def test_eligibility_labels(client):
    ids = seed_core()
    assert fit(client, ids, {"qualification": ids["bcom"]})[ids["role1"]]["eligibility"]["label"] == "eligible"
    not_listed = fit(client, ids, {"qualification": ids["btech"]})[ids["role1"]]["eligibility"]
    assert not_listed["label"] == "not_listed" and not_listed["listed_degrees"] == ["Test Degree A"]
    assert fit(client, ids, {"qualification": ids["bcom"]})[ids["role2"]]["eligibility"]["label"] == "open"
    assert fit(client, ids, {})[ids["role1"]]["eligibility"]["label"] == "unknown"


def test_compatibility_uses_interests_skills_and_education(client):
    ids = seed_core()
    strong = fit(client, ids, {"qualification": ids["bcom"], "interests": [ids["s1"]], "skills": [ids["skill"]]})
    assert strong[ids["role1"]]["compatibility"]["label"] == "strong"
    low = fit(client, ids, {"qualification": ids["btech"], "interests": [ids["s1"]]})
    assert low[ids["role2"]]["compatibility"]["label"] == "low"
    assert fit(client, ids, {})[ids["role1"]]["compatibility"]["label"] == "unknown"


def test_readiness_counts_by_tier_and_uses_checklist_and_skills(client):
    ids = seed_core()
    base = fit(client, ids, {})[ids["role1"]]["readiness"]
    assert base["by_tier"]["mandatory"] == {"done": 0, "total": 2}
    assert base["label"] == "substantial_preparation"
    # a reported skill and a ticked internship cover both mandatory items and the certificate
    done = fit(client, ids, {"skills": [ids["skill"]]}, completed=ids["req_ids"][1:3])[ids["role1"]]["readiness"]
    assert done["by_tier"]["mandatory"]["done"] == 2 and done["label"] == "close"
    assert done["outstanding"] == []


def test_opportunity_links_only(client):
    ids = seed_core()
    res = fit(client, ids, {})
    opp = res[ids["role1"]]["opportunity"]
    assert opp["label"] == "pages_listed" and opp["hiring_pages"][0]["careers_url"].startswith("https://")
    assert "do not show live openings" in opp["reasons"][0]
    assert res[ids["role2"]]["opportunity"]["label"] == "none_listed"


def test_sorting_by_chosen_answer(client):
    ids = seed_core()
    r = client.post("/v1/fit", json={"profile": {"qualification": ids["bcom"]}, "sort": "eligibility"}).json()
    assert r["results"][0]["role"]["slug"] == ids["role1"]  # eligible before open


def test_drafts_and_unpublished_sectors_never_appear(client):
    ids = seed_core()
    with session() as db:
        s = db.query(m.Sector).filter_by(slug=ids["s2"]).one()
        s.status = m.Status.draft
        db.add(m.Role(slug="draft-role", title="Draft Role", job_family="F", sector_id=s.id, description="d",
                      status=m.Status.draft))
        db.commit()
    res = fit(client, ids, {})
    assert ids["role2"] not in res and "draft-role" not in res and ids["role1"] in res


def test_invalid_profile_is_rejected(client):
    seed_core()
    r = client.post("/v1/fit", json={"profile": {"interests": ["Not A Slug!"]}})
    assert r.status_code == 422
    r = client.post("/v1/fit", json={"profile": {"year_of_study": 9}})
    assert r.status_code == 422

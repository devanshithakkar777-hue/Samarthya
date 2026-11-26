from datetime import date

import pytest
from sqlalchemy import select

from app import models as m
from .eval_ask_set import CASES
from .factories import make_source, published, session


@pytest.fixture()
def kb():
    with session() as db:
        src = make_source(db, "https://example.org/eval")
        qa = published(db, m.Qualification, src, slug="test-degree-a", degree="Test Degree A", level="undergraduate", duration_years=3)
        qb = published(db, m.Qualification, src, slug="test-degree-b", degree="Test Degree B", level="undergraduate", duration_years=4)
        sg = published(db, m.Sector, src, slug="glimmerwork", name="Glimmerwork", summary="Fake sector about glimmering things.")
        sn = published(db, m.Sector, src, slug="nimbleforge", name="Nimbleforge", summary="Fake sector about forging nimbly.")
        sk = published(db, m.Skill, src, slug="frobnication", name="Frobnication", category="Fake",
                       overview="Frobnication is a fake skill used only in tests.")
        published(db, m.LearningResource, src, skill_id=sk.id, title="Free Frob Course", provider="Fake Academy", url="https://example.org/f",
                  format="course", level="beginner", price_inr=0, language="English")
        roles = {}
        for slug, title, sector, deg in (("quillmaker", "Quillmaker", sg, qa), ("zorbwright", "Zorbwright", sn, qb),
                                         ("brindle-analyst", "Brindle Analyst", sg, qa), ("flumox-technician", "Flumox Technician", sn, qb)):
            r = published(db, m.Role, src, slug=slug, title=title, job_family="Fake family", sector_id=sector.id,
                          description=f"Fake role description for {title}.")
            db.add(m.RoleQualification(role_id=r.id, qualification_id=deg.id))
            db.add(m.RoleRequirement(role_id=r.id, type=m.RequirementType.subject, tier=m.Tier.mandatory, label="Fake subject", position=1))
            db.add(m.RoleRequirement(role_id=r.id, type=m.RequirementType.internship, tier=m.Tier.common_preference, label="One fake internship", position=2))
            roles[slug] = r
        for cslug, cname in (("wibblesworth", "Wibblesworth Industries"), ("pondercorp", "Pondercorp")):
            c = published(db, m.Company, src, slug=cslug, name=cname, summary=f"Fake company {cname}.")
            for rs in ("quillmaker", "zorbwright", "brindle-analyst"):
                db.add(m.CompanyRole(company_id=c.id, role_id=roles[rs].id, careers_url="https://example.org/careers",
                                     last_verified=date.today()))
        db.commit()


@pytest.mark.parametrize("question,path,phrase", CASES, ids=[c[0][:40] for c in CASES])
def test_eval_case(client, kb, question, path, phrase):
    r = client.post("/v1/ask", json={"question": question})
    assert r.status_code == 200, r.text
    out = r.json()
    if path is None:
        assert out["answered"] is False, f"should refuse, but answered: {out['answer']}"
        assert out["citations"] == [] or out.get("reason") == "gap"
    else:
        assert out["answered"] is True, f"should answer: {out}"
        assert any(c["path"] == path for c in out["citations"]), f"wrong citation: {out['citations']}"
        assert phrase.lower() in out["answer"].lower(), out["answer"]
        assert all(c["source"] for c in out["citations"]), "every citation carries its source"


def test_unanswered_questions_are_recorded_without_identity(client, kb):
    client.post("/v1/ask", json={"question": "What is quantum chromodynamics?"})
    client.post("/v1/ask", json={"question": "what is quantum chromodynamics"})
    with session() as db:
        rows = db.scalars(select(m.UnansweredQuestion)).all()
    assert len(rows) == 1 and rows[0].times_asked == 2


def test_refusal_text_is_plain(client, kb):
    out = client.post("/v1/ask", json={"question": "Tell me a joke"}).json()
    assert out["answer"].startswith("I do not have a sourced answer")


def test_ask_is_rate_limited(client, kb):
    codes = [client.post("/v1/ask", json={"question": "Tell me about Quillmaker"}).status_code for _ in range(25)]
    assert 429 in codes


def test_ask_rejects_bad_input(client):
    assert client.post("/v1/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/v1/ask", json={"question": "x" * 400}).status_code == 422

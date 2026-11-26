from app import models as m
from .factories import make_source, published, session


def _seed():
    with session() as db:
        src = make_source(db)
        published(db, m.Qualification, src, slug="test-ba", degree="Test BA", level="undergraduate", kind="degree",
                  stream="Humanities and Arts", duration_years=3)
        published(db, m.Qualification, src, slug="test-ca", degree="Test CA", level="unspecified",
                  kind="professional_qualification", stream="Commerce", awarding_body="Test Institute")
        published(db, m.Qualification, src, slug="test-phd", degree="Test PhD", level="doctoral", kind="degree", stream="Law")
        published(db, m.Qualification, src, slug="test-iti", degree="Test ITI trade", level="unspecified", kind="certificate",
                  stream="Vocational")
        draft = m.Qualification(slug="test-draft", degree="Hidden draft", level="undergraduate", kind="degree",
                                source_id=src.id, last_verified=src.id and __import__("datetime").date.today())
        db.add(draft)
        db.commit()


def test_filters_and_hidden_drafts(client):
    _seed()
    r = client.get("/v1/pathways").json()
    assert {i["slug"] for i in r["items"]} == {"test-ba", "test-ca", "test-phd", "test-iti"}
    assert client.get("/v1/pathways", params={"kind": "professional_qualification"}).json()["items"][0]["awarding_body"] == "Test Institute"
    assert [i["slug"] for i in client.get("/v1/pathways", params={"stream": "Law"}).json()["items"]] == ["test-phd"]
    assert [i["slug"] for i in client.get("/v1/pathways", params={"q": "iti"}).json()["items"]] == ["test-iti"]
    assert [i["slug"] for i in client.get("/v1/pathways", params={"stage": "research"}).json()["items"]] == ["test-phd"]
    assert {i["slug"] for i in client.get("/v1/pathways", params={"stage": "after-10"}).json()["items"]} == {"test-iti"}
    assert {i["slug"] for i in client.get("/v1/pathways", params={"stage": "after-12"}).json()["items"]} == {"test-ba", "test-ca", "test-iti"}
    assert client.get("/v1/pathways", params={"stage": "nonsense"}).status_code == 422


def test_facets_ignore_their_own_filter(client):
    _seed()
    r = client.get("/v1/pathways", params={"stream": "Law"}).json()
    assert r["streams"]["Commerce"] == 1 and r["kinds"]["degree"] == 2  # counts not narrowed by the stream filter


def test_detail_states_what_is_not_verified(client):
    _seed()
    d = client.get("/v1/pathways/test-ca").json()
    assert d["awarding_body"] == "Test Institute" and "eligibility" in d["not_yet_verified"]
    assert d["source"]["url"] == "https://example.org/source"
    assert client.get("/v1/pathways/test-draft").status_code == 404


def test_unassigned_stream_filter(client):
    _seed()
    with session() as db:
        published(db, m.Qualification, db.query(m.Source).first(), slug="test-nostream", degree="No stream degree", level="undergraduate", kind="degree")
        db.commit()
    assert [i["slug"] for i in client.get("/v1/pathways", params={"stream": "Not yet assigned"}).json()["items"]] == ["test-nostream"]


def test_detail_fields_leave_the_unverified_list_once_filled(client):
    _seed()
    with session() as db:
        q = db.query(m.Qualification).filter_by(slug="test-ca").one()
        q.eligibility = "Class 12 pass"
        q.official_url = "https://example.org/ca"
        db.commit()
    d = client.get("/v1/pathways/test-ca").json()
    assert d["eligibility"] == "Class 12 pass" and d["official_url"] == "https://example.org/ca"
    assert "eligibility" not in d["not_yet_verified"] and "recognition" in d["not_yet_verified"]
